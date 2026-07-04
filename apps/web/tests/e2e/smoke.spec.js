import { expect, test } from "@playwright/test";

const API_BASE = "http://localhost:8081";

async function mockApp(page) {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "mykb.auth",
      JSON.stringify({ token: "mock-token", user: { id: "user-1", username: "yorushika" } })
    );
  });

  await page.route(`${API_BASE}/api/v1/**`, async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [{ id: "kb-1", name: "test", description: "mock kb", accessType: "OWNER" }]
        })
      });
      return;
    }

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: { id: "kb-1", name: "test", description: "mock kb", accessType: "OWNER" } })
      });
      return;
    }

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1/documents") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            { id: "doc-1", originalFilename: "alpha.txt", sizeBytes: 272, contentType: "text/plain", processingStatus: "SUCCEEDED" },
            { id: "doc-2", originalFilename: "beta.txt", sizeBytes: 106, contentType: "text/plain", processingStatus: "SUCCEEDED" }
          ]
        })
      });
      return;
    }

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1/ingestion-tasks") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ data: [] }) });
      return;
    }

    if (request.method() === "POST" && pathname === "/api/v1/knowledge-bases/kb-1/qa") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            answer: "alpha 文档说明项目使用 pgvector 做向量检索。",
            sources: [{ documentId: "doc-1", documentName: "alpha.txt", chunkIndex: 0, score: 0.86, preview: "pgvector 做向量检索" }],
            hitCount: 1,
            latencyMs: 18,
            refused: false
          }
        })
      });
      return;
    }

    await route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ message: `unhandled mock route: ${request.method()} ${pathname}` }) });
  });
}

test.beforeEach(async ({ page }) => {
  await mockApp(page);
});

test("workspace keeps chat and documents reachable", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("智能知识库").first()).toBeVisible();
  await expect(page.getByPlaceholder("向您的文档提问…")).toBeVisible();

  await page.getByRole("button", { name: "文档" }).click();
  await expect(page.getByRole("heading", { name: /文档/ })).toBeVisible();
  await expect(page.getByText("alpha.txt")).toBeVisible();

  await page.getByRole("button", { name: "对话" }).click();
  await page.getByPlaceholder("向您的文档提问…").fill("项目怎么检索？");
  await page.keyboard.press("Enter");

  await expect(page.getByText("alpha 文档说明项目使用 pgvector 做向量检索。")).toBeVisible();
  await expect(page.getByText("命中 1 · 18ms")).toBeVisible();
});

test("primary controls do not overflow at common breakpoints", async ({ page }) => {
  for (const viewport of [
    { width: 1440, height: 960 },
    { width: 1024, height: 820 },
    { width: 390, height: 844 }
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/");
    await expect(page.getByPlaceholder("向您的文档提问…")).toBeVisible();

    const hasHorizontalOverflow = await page.evaluate(() => {
      const root = document.documentElement;
      return root.scrollWidth - root.clientWidth > 1;
    });
    expect(hasHorizontalOverflow).toBe(false);
  }
});

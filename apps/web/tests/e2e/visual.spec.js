import { expect, test } from "@playwright/test";

const API_BASE = "http://localhost:8081";

test.beforeEach(async ({ page }) => {
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
        body: JSON.stringify({ data: [{ id: "kb-1", name: "test", description: "mock kb", accessType: "OWNER" }] })
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
          data: [{ id: "doc-1", originalFilename: "alpha.txt", sizeBytes: 272, contentType: "text/plain", processingStatus: "SUCCEEDED" }]
        })
      });
      return;
    }
    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1/ingestion-tasks") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ data: [] }) });
      return;
    }

    await route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ message: `unhandled mock route: ${request.method()} ${pathname}` }) });
  });
});

test("desktop workbench has stable product structure", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto("/");

  await expect(page.getByText("智能知识库").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "对话" })).toBeVisible();
  await expect(page.getByRole("button", { name: "文档" })).toBeVisible();
  await expect(page.getByPlaceholder("向您的文档提问…")).toBeVisible();

  await page.getByRole("button", { name: "文档" }).click();
  await expect(page.getByRole("heading", { name: /文档/ })).toBeVisible();
  await expect(page.getByText("alpha.txt")).toBeVisible();
});

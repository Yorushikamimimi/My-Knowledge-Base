import { expect, test } from "@playwright/test";

const API_BASE = "http://localhost:8081";

async function mockApp(page) {
  await page.addInitScript(() => {
    const auth = {
      token: "mock-token",
      user: { id: "user-1", username: "yorushika" }
    };
    window.localStorage.setItem("mykb.auth", JSON.stringify(auth));
  });

  await page.route(`${API_BASE}/api/v1/**`, async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "kb-1",
              name: "test",
              description: "mock kb",
              accessType: "OWNER",
              createdAt: "2026-03-20T00:00:00.000Z",
              updatedAt: "2026-03-23T00:00:00.000Z",
              documentCount: 3
            }
          ]
        })
      });
      return;
    }

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            id: "kb-1",
            name: "test",
            description: "mock kb",
            accessType: "OWNER"
          }
        })
      });
      return;
    }

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1/documents") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "doc-1",
              originalFilename: "alpha.txt",
              sizeBytes: 272,
              contentType: "text/plain",
              processingStatus: "SUCCEEDED",
              createdAt: "2026-03-20T00:00:00.000Z"
            },
            {
              id: "doc-2",
              originalFilename: "beta.txt",
              sizeBytes: 106,
              contentType: "text/plain",
              processingStatus: "SUCCEEDED",
              createdAt: "2026-03-20T01:00:00.000Z"
            },
            {
              id: "doc-3",
              originalFilename: "failed.txt",
              sizeBytes: 64,
              contentType: "text/plain",
              processingStatus: "FAILED",
              createdAt: "2026-03-20T02:00:00.000Z"
            }
          ]
        })
      });
      return;
    }

    if (request.method() === "GET" && pathname === "/api/v1/knowledge-bases/kb-1/ingestion-tasks") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "task-1",
              taskType: "DOCUMENT_INGESTION",
              status: "FAILED",
              currentStage: "UPLOAD",
              createdAt: "2026-03-20T03:00:00.000Z",
              failureMessage: "Mock upload failure"
            },
            {
              id: "task-2",
              taskType: "DOCUMENT_INGESTION",
              status: "SUCCEEDED",
              currentStage: "COMPLETED",
              createdAt: "2026-03-20T04:00:00.000Z",
              failureMessage: null
            }
          ]
        })
      });
      return;
    }

    if (request.method() === "DELETE" && pathname === "/api/v1/knowledge-bases/kb-1/documents/doc-3") {
      await route.fulfill({ status: 204, body: "" });
      return;
    }

    if (request.method() === "POST" && pathname === "/api/v1/knowledge-bases/kb-1/ingestion-tasks/task-1/retry") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: { accepted: true } })
      });
      return;
    }

    if (request.method() === "POST" && pathname === "/api/v1/knowledge-bases/kb-1/qa") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: {
            answer: "alpha 文档说明项目使用 pgvector 做向量检索。",
            sources: [
              {
                documentId: "doc-1",
                documentName: "alpha.txt",
                chunkIndex: 0,
                score: 0.86,
                preview: "pgvector 做向量检索"
              }
            ],
            hitCount: 1,
            latencyMs: 18,
            refused: false
          }
        })
      });
      return;
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ message: `unhandled mock route: ${request.method()} ${pathname}` })
    });
  });
}

test.beforeEach(async ({ page }) => {
  await mockApp(page);
});

test("workspace exposes document status and json qa sources", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "文档" }).click();
  await expect(page.getByRole("heading", { name: /文档/ })).toBeVisible();
  await expect(page.getByText("failed.txt")).toBeVisible();
  await expect(page.getByRole("button", { name: "删除", exact: true })).toBeVisible();
  await expect(page.getByText("Mock upload failure")).toBeVisible();
  await expect(page.getByRole("button", { name: "重试" })).toBeVisible();

  await page.getByRole("button", { name: "对话" }).click();
  await page.getByPlaceholder("向您的文档提问…").fill("项目怎么检索？");
  await page.keyboard.press("Enter");

  await expect(page.getByText("alpha 文档说明项目使用 pgvector 做向量检索。")).toBeVisible();
  await expect(page.getByText("命中 1 · 18ms")).toBeVisible();
  await expect(page.getByText("alpha.txt")).toBeVisible();
});

import * as fs from "fs"
import * as path from "path"
import { fileURLToPath } from "url"
import { test, expect } from "@playwright/test"

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OASF_DIR = path.join(__dirname, "../../../../oasf/agents")

function loadOasfFixture(slug: string): Record<string, unknown> {
  const file = path.join(OASF_DIR, `${slug}.json`)
  const raw = fs.readFileSync(file, "utf-8")
  return JSON.parse(raw) as Record<string, unknown>
}

test.describe("OASF directory modal", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/agents/*/oasf", async (route) => {
      const url = route.request().url()
      const match = url.match(/\/agents\/([^/]+)\/oasf/)
      const slug = match ? match[1] : ""
      const fixtures: Record<string, Record<string, unknown>> = {
        "exchange-supervisor-agent": loadOasfFixture("exchange-supervisor-agent"),
        "flavor-profile-farm-agent": loadOasfFixture("flavor-profile-farm-agent"),
      }
      const body = slug && fixtures[slug] ? fixtures[slug] : { name: "Unknown" }
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) })
    })
  })

  test("graph loads with two nodes and directory button opens OASF modal with inline record", async ({
    page,
  }) => {
    await page.goto("/")

    const supervisorNode = page.getByText("Supervisor Agent").first()
    await expect(supervisorNode).toBeVisible({ timeout: 15_000 })

    const graderNode = page.getByText("Grader Agent").first()
    await expect(graderNode).toBeVisible()

    const directoryIcon = page.getByRole("button", { name: "AGNTCY Directory" }).first()
    await expect(directoryIcon).toBeVisible()
    await directoryIcon.click()

    const modal = page.locator("[data-modal-content]")
    await expect(modal).toBeVisible({ timeout: 10_000 })
    await expect(modal).toContainText("OASF Record")
    await expect(modal.locator("pre")).toBeVisible()

    await expect(modal.getByRole("link", { name: /view in directory/i })).toHaveCount(0)
  })

  test("directory button on Grader Agent node opens OASF modal with farm agent record", async ({
    page,
  }) => {
    await page.goto("/")

    await expect(page.getByText("Grader Agent").first()).toBeVisible({ timeout: 15_000 })

    const directoryButtons = page.getByRole("button", { name: "AGNTCY Directory" })
    await expect(directoryButtons).toHaveCount(2)
    await directoryButtons.nth(1).click()

    const modal = page.locator("[data-modal-content]")
    await expect(modal).toBeVisible({ timeout: 10_000 })
    await expect(modal).toContainText("OASF Record")
    await expect(modal.locator("pre")).toContainText("Coffee Farm Flavor Agent")
    await expect(modal.getByRole("link", { name: /view in directory/i })).toHaveCount(0)
  })
})

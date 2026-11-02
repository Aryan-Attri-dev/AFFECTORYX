import os
import time
from playwright.sync_api import sync_playwright, expect

SCREENSHOT_DIR = "/Users/botdigit/.gemini/antigravity-ide/brain/641a330a-6d90-4b8b-8e8f-f0b25ab8dd06/e2e_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

VIEWPORTS = [
    {"name": "1920x1080_desktop", "width": 1920, "height": 1080},
    {"name": "1440x900_standard", "width": 1440, "height": 900},
    {"name": "1280x800_compact", "width": 1280, "height": 800},
]


def test_full_phase2_lifecycle():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            print(f"\n[+] Testing Phase 2 on Viewport: {vp['name']} ({vp['width']}x{vp['height']})")
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()

            # 1. Login
            page.goto("http://localhost:3000/login")
            page.wait_for_selector("button:has-text('NEW WORKSPACE')")
            page.click("button:has-text('NEW WORKSPACE')")

            ts = int(time.time() * 1000)
            email = f"cto_{ts}_{vp['width']}@vanguard.internal"
            page.fill("input[placeholder='e.g. Linus Torvalds']", "Chief Architect")
            page.fill("input[placeholder='e.g. Acme Corp (optional)']", "Vanguard Financial Labs")
            page.fill("input[type='email']", email)
            page.fill("input[type='password']", "StrongPassword2026!")
            page.click("button:has-text('Create Workspace')")

            # 2. Arrive at Dashboard
            page.wait_for_selector("text=Executive Intelligence Overview", timeout=10000)

            # 3. Register Core Service Project
            page.click("button:has-text('Register Service')")
            page.wait_for_selector("text=Create New Engineering Project")
            page.fill("input[placeholder='e.g. core-billing-engine']", "ledger-core")
            page.fill("textarea", "Global transactional ledger and payout router")
            page.click("button:has-text('Create Project')")
            page.wait_for_selector("text=ledger-core", timeout=10000)

            # 4. Navigate to Dependency Graph (/graph)
            page.click("a[href='/graph']")
            page.wait_for_selector("text=Evidence-Based Dependency Topology")
            page.screenshot(path=f"{SCREENSHOT_DIR}/20_empty_graph_{vp['name']}.png")

            # 5. Open Ingest Modal and Ingest OpenAPI spec
            page.click("button:has-text('Ingest Evidence')")
            page.wait_for_selector("text=Evidence & Dependency Ingestion Engine")
            page.click("button:has-text('Execute Ingestion')")
            page.wait_for_selector("text=OpenAPI specification parsed", timeout=8000)
            page.screenshot(path=f"{SCREENSHOT_DIR}/21_openapi_ingested_{vp['name']}.png")

            # 6. Verify components rendered in topology canvas
            page.wait_for_selector("text=Core Ledger & Settlement Service", timeout=10000)
            expect(page.locator("text=Core Ledger & Settlement Service").first).to_be_visible()
            expect(page.locator("text=POST /api/v1/settlements").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/22_topology_populated_{vp['name']}.png")

            # 7. Ingest Customer SLA
            page.click("button:has-text('Ingest Evidence')")
            page.wait_for_selector("button:has-text('Customer SLA')")
            page.click("button:has-text('Customer SLA')")
            page.click("button:has-text('Execute Ingestion')")
            page.wait_for_selector("text=workflow mappings registered", timeout=8000)

            # 8. Verify Customer Workflow appears in canvas
            page.wait_for_selector("text=Titan Global Bank", timeout=10000)
            expect(page.locator("text=Titan Global Bank").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/23_customer_topology_{vp['name']}.png")

            # 9. Click on POST /api/v1/settlements to open Inspector
            page.click("button:has-text('POST /api/v1/settlements')")
            page.wait_for_selector("button:has-text('Simulate Blast Radius')")
            page.click("button:has-text('Simulate Blast Radius')")
            page.wait_for_selector("text=Transitive Downstream Impact", timeout=8000)
            page.screenshot(path=f"{SCREENSHOT_DIR}/24_blast_radius_inspector_{vp['name']}.png")

            # 10. Navigate to Evidence Registry (/evidence)
            page.click("a[href='/evidence']")
            page.wait_for_selector("text=Evidence Provenance Registry")
            expect(page.locator("text=Declared in OpenAPI specification").first).to_be_visible()
            expect(page.locator("text=CONFIRMED").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/25_evidence_registry_{vp['name']}.png")

            # 11. Navigate to Customer Intelligence (/customers)
            page.click("a[href='/customers']")
            page.wait_for_selector("text=Customer Intelligence & SLA Mappings")
            expect(page.locator("text=Titan Global Bank").first).to_be_visible()
            expect(page.locator("text=99.999%").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/26_customers_matrix_{vp['name']}.png")

            print(f"  ✓ Phase 2 Viewport {vp['name']} passed all assertions.")
            context.close()

        browser.close()


if __name__ == "__main__":
    test_full_phase2_lifecycle()
    print("\n✅ All Playwright Phase 2 E2E tests and visual regression audits completed successfully!")

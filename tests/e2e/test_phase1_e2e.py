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


def test_full_phase1_lifecycle():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            print(f"\n[+] Testing Viewport: {vp['name']} ({vp['width']}x{vp['height']})")
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()

            # 1. Access Root (Redirects to /login)
            page.goto("http://localhost:3000")
            page.wait_for_selector("text=AFFECTORYX")
            expect(page.locator("text=AFFECTORYX").first).to_be_visible()
            expect(page.locator("p:has-text('ENGINEERING INTELLIGENCE PLATFORM')")).to_be_visible()
            expect(page.locator("footer:has-text('Aryan Attri')")).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/01_login_page_{vp['name']}.png")

            # 2. Switch to NEW WORKSPACE tab
            page.click("button:has-text('NEW WORKSPACE')")
            page.wait_for_selector("text=Full Name")
            page.screenshot(path=f"{SCREENSHOT_DIR}/02_register_tab_{vp['name']}.png")

            # 3. Fill registration form
            ts = int(time.time() * 1000)
            email = f"alexander_{ts}_{vp['width']}@hyperion.internal"
            page.fill("input[placeholder='e.g. Linus Torvalds']", "Dr. Alexander Wright")
            page.fill("input[placeholder='e.g. Acme Corp (optional)']", "Hyperion Defense Labs")
            page.fill("input[type='email']", email)
            page.fill("input[type='password']", "StrongPassword2026!")

            # 4. Click Submit
            page.click("button:has-text('Create Workspace')")

            # 5. Verify redirect to dashboard via SPA locator
            page.wait_for_selector("text=Executive Intelligence Overview", timeout=10000)
            expect(page.locator("text=Executive Intelligence Overview")).to_be_visible()
            expect(page.locator("text=Hyperion Defense Labs").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/03_dashboard_{vp['name']}.png")

            # 6. Open Register Service Modal
            page.click("button:has-text('Register Service')")
            page.wait_for_selector("text=Create New Engineering Project")
            expect(page.locator("text=Create New Engineering Project")).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/04_create_modal_{vp['name']}.png")

            # 7. Fill Service details
            page.fill("input[placeholder='e.g. core-billing-engine']", "payments-core")
            page.fill("textarea", "Mission-critical payment settlement and ledger microservice")
            page.fill("input[type='url']", "https://github.com/hyperion/payments-core")
            page.fill("input[value='production, staging']", "production, staging, disaster-recovery")

            # 8. Submit modal
            page.click("button:has-text('Create Project')")

            # 9. Verify project created and appears in catalog preview
            page.wait_for_selector("text=payments-core", timeout=10000)
            expect(page.locator("text=payments-core").first).to_be_visible()
            expect(page.locator("text=production").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/05_project_created_{vp['name']}.png")

            # 10. Navigate to Projects page
            page.click("a[href='/projects']")
            page.wait_for_selector("text=Projects & Microservice Systems")
            expect(page.locator("text=Projects & Microservice Systems")).to_be_visible()
            expect(page.locator("text=payments-core").first).to_be_visible()
            expect(page.locator("text=disaster-recovery").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/06_projects_catalog_{vp['name']}.png")

            # 11. Test Search Filter
            page.fill("input[placeholder='Filter services or repositories...']", "payments")
            expect(page.locator("text=payments-core").first).to_be_visible()

            page.fill("input[placeholder='Filter services or repositories...']", "nonexistent-xyz")
            expect(page.locator("text=No projects registered yet")).to_be_visible()

            page.fill("input[placeholder='Filter services or repositories...']", "")
            expect(page.locator("text=payments-core").first).to_be_visible()

            # 12. Navigate to Settings Page
            page.click("a[href='/settings']")
            page.wait_for_selector("text=Organization & Security Settings")
            expect(page.locator("text=Organization & Security Settings")).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/07_settings_general_{vp['name']}.png")

            # Check Members Tab
            page.click("button:has-text('Team Members')")
            page.wait_for_selector("text=Dr. Alexander Wright")
            expect(page.locator("text=Dr. Alexander Wright").first).to_be_visible()
            expect(page.locator("text=Owner").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/08_settings_members_{vp['name']}.png")

            # Check Security Audit Logs Tab
            page.click("button:has-text('Security Audit Logs')")
            page.wait_for_selector("text=auth.register")
            expect(page.locator("text=auth.register").first).to_be_visible()
            expect(page.locator("text=project.create").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/09_settings_audit_{vp['name']}.png")

            # 13. Navigate to Audit Page
            page.click("a[href='/audit']")
            page.wait_for_selector("text=Enterprise Audit Trail & Security Log")
            expect(page.locator("text=Enterprise Audit Trail & Security Log")).to_be_visible()
            expect(page.locator("text=project.create").first).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/10_audit_page_{vp['name']}.png")

            # 14. Sign Out
            page.click("button:has-text('Dr. Alexander Wright')")
            page.click("button:has-text('Sign out')")
            page.wait_for_selector("text=Sign In to Console")
            expect(page.get_by_role("button", name="SIGN IN", exact=True)).to_be_visible()
            page.screenshot(path=f"{SCREENSHOT_DIR}/11_signed_out_{vp['name']}.png")

            print(f"  ✓ Viewport {vp['name']} passed all assertions.")
            context.close()

        browser.close()


if __name__ == "__main__":
    test_full_phase1_lifecycle()
    print("\n✅ All Playwright Phase 1 E2E tests and multi-viewport visual audits completed successfully!")

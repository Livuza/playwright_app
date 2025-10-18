# Copyright (c) 2025, Livuza and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

# Safe import for Playwright
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


class PlaywrightTest(Document):
    pass
@frappe.whitelist()
def run_login(docname):
    if not sync_playwright:
        frappe.throw("Playwright is not installed. Please run: <code>python3 -m playwright install</code>")

    doc = frappe.get_doc("Playwright Test", docname)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
            page = browser.new_page()

            page.goto("https://practicetestautomation.com/practice-test-login/", timeout=60000)

            # Debug: log DOM
            frappe.logger().info(page.content())

            # Accept cookies if popup appears
            try:
                page.click("text=Accept", timeout=3000)
            except:
                pass

            # Wait for username field
            page.wait_for_selector("input#username", timeout=15000)
            page.fill("input#username", "student")
            page.fill("input#password", "Password123")

            # Make button visible before clicking
            button = page.locator("button[type='submit']")
            button.wait_for(state="visible", timeout=15000)
            button.click()

            page.wait_for_selector(".post-title", timeout=15000)
            result = page.text_content(".post-title")

            doc.status = "Success"
            doc.log_output = result or "Login successful but no result text found"
            browser.close()

    except Exception as e:
        doc.status = "Failed"
        doc.log_output = f"Playwright error: {str(e)}"

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return f"Playwright test completed: {doc.status}"


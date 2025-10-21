# Copyright (c) 2025, Livuza and contributors
# For license information, please see license.txt

import frappe
import tempfile
import shutil
import time
from frappe.model.document import Document

try:
	from playwright.sync_api import sync_playwright
except ImportError:
	sync_playwright = None


class PlaywrightTest(Document):
	"""DocType for running Playwright login tests."""
	pass


@frappe.whitelist()
def run_login(docname: str) -> str:
	"""Run Playwright login test with optimized flow, speed, and cleanup."""
	if not sync_playwright:
		frappe.throw(
			"Playwright is not installed.<br>"
			"Please run: <code>pip install playwright && python3 -m playwright install</code>"
		)

	doc = frappe.get_doc("Playwright Test", docname)
	temp_dir = tempfile.mkdtemp(prefix="playwright_user_data_")
	browser = None

	try:
		with sync_playwright() as p:
			frappe.logger().info("Launching Chromium browser for Playwright test...")

			# Launch browser context
			browser = p.chromium.launch_persistent_context(
				user_data_dir=temp_dir,
				headless=False,
				args=[
					"--no-sandbox",
					"--disable-dev-shm-usage",
					"--disable-blink-features=AutomationControlled",
				],
			)

			page = browser.new_page()

			# Load target page
			page.goto("https://practicetestautomation.com/practice-test-login/", timeout=60_000)
			page.wait_for_load_state("networkidle", timeout=2_000)
			frappe.logger().info("Login page loaded successfully.")

			# Handle cookie pop-up
			try:
				page.click("text=Accept", timeout=3_000)
				frappe.logger().info("Cookie popup accepted.")
			except Exception:
				pass

			# Wait for username field
			page.wait_for_selector("input#username", timeout=2_000)

			# Input Credentials
			username_input = page.locator("input#username")
			password_input = page.locator("input#password")

			username_input.type("student", delay=5)
			password_input.type("Password123", delay=5)

			# Click Login Button
			try:
				page.click("button[type='submit']", timeout=2_000, force=True)
			except Exception as e:
				frappe.logger().warning(f"Standard button click failed: {e}. Retrying via XPath selector.")
				page.click("xpath=//button[contains(., 'Submit')]", timeout=2_000, force=True)

			# Wait for post-login content
			page.wait_for_load_state("networkidle", timeout=2_000)
			time.sleep(3)

			result = None
			try:
				result = page.text_content(".post-title", timeout=2_000)
			except Exception:
				try:
					result = page.text_content("text=Logged In Successfully", timeout=2_000)
				except Exception:
					pass

			doc.status = "Success" if result else "Failed"
			doc.log_output = result or "Login attempt completed but success text not found."

			frappe.logger().info(f"Playwright test completed for {docname}: {doc.status} -> {doc.log_output}")

	except Exception as e:
		doc.status = "Failed"
		doc.log_output = f"Playwright error: {str(e)}"
		frappe.logger().error(f"Playwright test failed for {docname}: {e}")

	finally:
		if browser:
			try:
				browser.close()
				frappe.logger().info("Browser closed successfully.")
			except Exception:
				pass

		shutil.rmtree(temp_dir, ignore_errors=True)
		frappe.logger().info("Temporary user data directory cleaned up.")

		doc.save(ignore_permissions=True)
		frappe.db.commit()

	return f"Playwright test completed: {doc.status}"

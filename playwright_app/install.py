import subprocess
import sys
import frappe

def after_install():
    frappe.logger().info("Installing Playwright dependency...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright==1.55.0"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        frappe.logger().info("Playwright and browsers installed successfully.")
    except Exception as e:
        frappe.logger().error(f"Playwright installation failed: {e}")

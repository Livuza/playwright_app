import subprocess
import sys
import platform
import frappe

def after_install():
    """Install Playwright Python package, browsers, and required system dependencies."""
    frappe.logger().info("Starting Playwright setup...")

    try:
        # Install Playwright Python package
        frappe.logger().info("Installing Playwright Python module...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright==1.55.0"])

        # Install browser binaries
        frappe.logger().info("Installing Playwright browsers...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])

        # Install required system dependencies (for Linux)
        if platform.system().lower() == "linux":
            frappe.logger().info("Installing system dependencies for Playwright...")
            try:
                subprocess.check_call([
                    "sudo", "apt-get", "install", "-y",
                    "libatk1.0-0",
                    "libatk-bridge2.0-0",
                    "libxkbcommon0",
                    "libatspi2.0-0",
                    "libxcomposite1",
                    "libxdamage1",
                    "libxfixes3",
                    "libxrandr2",
                    "libgbm1",
                    "libasound2"
                ])
            except subprocess.CalledProcessError as e:
                frappe.logger().warning(f"Could not install apt packages automatically: {e}")
                frappe.logger().warning("You may need to run manually: sudo playwright install-deps")

        frappe.logger().info("Playwright installation and dependencies setup completed successfully.")

    except Exception as e:
        frappe.logger().error(f"Playwright setup failed: {e}")
        frappe.throw(f"Playwright setup failed: {e}")

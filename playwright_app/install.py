import subprocess
import sys
import platform
import shutil
import os
import frappe

def run_command(cmd, description):
    """Helper to run shell commands safely and log progress."""
    try:
        subprocess.check_call(cmd)
        frappe.logger().info(f"{description} completed successfully.")
    except subprocess.CalledProcessError as e:
        frappe.logger().error(f"Failed during {description}: {e}")
        raise

def after_install():
    """Install Playwright, browser binaries, and required system dependencies."""
    frappe.logger().info("Starting Playwright setup process...")

    # Install Playwright package
    run_command(
        [sys.executable, "-m", "pip", "install", "playwright==1.55.0"],
        "Installing Playwright Python module"
    )

    # Install required system libraries (for Linux)
    if platform.system().lower() == "linux":
        deps = [
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
        ]
        # Detect if sudo is available
        sudo_prefix = ["sudo"] if shutil.which("sudo") else []
        run_command(sudo_prefix + ["apt-get", "update"], "Updating apt repository")
        run_command(sudo_prefix + ["apt-get", "install", "-y"] + deps, "Installing Playwright system dependencies")

    # Ensure browser binaries are downloaded
    # Run playwright install explicitly as frappe user (not root)
    playwright_bin = shutil.which("playwright")
    if not playwright_bin:
        playwright_bin = f"{sys.executable} -m playwright"

    try:
        run_command(["sudo", "-u", "frappe", "bash", "-c", "playwright install"], "Installing Playwright browsers for frappe user")
    except Exception:
        frappe.logger().warning("Retrying browser installation without sudo...")
        run_command([sys.executable, "-m", "playwright", "install"], "Installing Playwright browsers (fallback)")

    # Verify that Chromium binary exists
    cache_dir = os.path.expanduser("~/.cache/ms-playwright")
    chromium_path = os.path.join(cache_dir, "chromium-1187", "chrome-linux", "chrome")
    if not os.path.exists(chromium_path):
        frappe.logger().warning("Chromium binary not found — forcing reinstallation.")
        run_command([sys.executable, "-m", "playwright", "install", "chromium"], "Installing Chromium binary")

    frappe.logger().info("Playwright setup completed successfully for frappe environment.")

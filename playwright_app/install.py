import subprocess
import sys
import platform
import os
import shutil
import getpass
import frappe


def run_command(cmd, description):
	"""Helper to run a shell command with logging."""
	frappe.logger().info(f"{description}...")
	try:
		subprocess.check_call(cmd)
		frappe.logger().info(f"{description} completed successfully.")
	except subprocess.CalledProcessError as e:
		frappe.logger().error(f"Failed during {description}: {e}")
		raise


def after_install():
	"""Install Playwright and required system/browser dependencies safely."""
	frappe.logger().info("Starting Playwright setup...")

	current_user = getpass.getuser()
	frappe.logger().info(f"Detected current user: {current_user}")

	# Install Playwright Python module
	run_command(
		[sys.executable, "-m", "pip", "install", "playwright==1.55.0"],
		"Installing Playwright Python module"
	)

	# Install Linux dependencies (if applicable)
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
			"libasound2",
		]
		if shutil.which("apt-get"):
			try:
				run_command(["apt-get", "update"], "Updating apt repository")
				run_command(["apt-get", "install", "-y"] + deps, "Installing Playwright system dependencies")
			except Exception as e:
				frappe.logger().warning(f"Could not install system packages: {e}")
				frappe.logger().warning("You may need to run manually: sudo playwright install-deps")
		else:
			frappe.logger().warning("apt-get not available — skipping system dependency installation.")

	# Install Playwright browsers for the active user
	home_dir = os.path.expanduser(f"~{current_user}")
	cache_dir = os.path.join(home_dir, ".cache", "ms-playwright")
	os.makedirs(cache_dir, exist_ok=True)

	try:
		run_command(
			["sudo", "-u", current_user, "bash", "-c", "playwright install chromium"],
			f"Installing Chromium for user '{current_user}'"
		)
	except Exception as e:
		frappe.logger().warning(f"Running as '{current_user}' failed: {e}, retrying directly.")
		run_command([sys.executable, "-m", "playwright", "install", "chromium"], "Installing Chromium directly")

	# Validate Chromium binary path
	expected_path = os.path.join(cache_dir, "chromium-1187", "chrome-linux", "chrome")
	if os.path.exists(expected_path):
		frappe.logger().info(f"Chromium installed successfully at {expected_path}")
	else:
		frappe.logger().warning(f"Chromium not found at {expected_path}")
		frappe.logger().info(
			f"Run manually as the active user:\n    playwright install chromium"
		)

	frappe.logger().info("Playwright setup completed successfully.")

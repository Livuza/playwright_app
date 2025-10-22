import frappe
import sys
import subprocess
import click
import os
from pathlib import Path

def after_install():
    """Main installation hook executed after the app is installed."""
    click.echo("Starting full Playwright + Chromium setup...")

    try:
        install_playwright_package()
        install_system_dependencies()
        # Explicitly run playwright install to download browsers
        install_playwright_browsers()
        # Optionally, run install-deps if permitted
        install_playwright_deps()
        click.secho("Playwright and browser setup completed successfully!", fg="green", bold=True)
    except Exception as e:
        frappe.log_error(title="Playwright Setup Error", message=str(e))
        click.secho(f"Playwright setup failed: {e}", fg="red", bold=True)

def install_playwright_package():
    """Install Playwright Python package."""
    click.echo("Installing Playwright Python package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "playwright"])
    click.echo("Playwright Python package installed.")

def install_system_dependencies():
    """Install Playwright system dependencies (Ubuntu 20–24 + Cloud safe)."""
    click.echo("Installing system dependencies...")

    try:
        os_release = subprocess.check_output(["lsb_release", "-rs"], text=True).strip()
    except Exception:
        os_release = "unknown"

    t64 = "24" in os_release or "noble" in os_release.lower()

    base_deps = [
        f"libatk1.0-0{'t64' if t64 else ''}",
        f"libatk-bridge2.0-0{'t64' if t64 else ''}",
        "libxkbcommon0",
        f"libatspi2.0-0{'t64' if t64 else ''}",
        "libxcomposite1",
        "libxdamage1",
        "libxfixes3",
        "libxrandr2",
        "libgbm1",
        f"libasound2{'t64' if t64 else ''}",
        "libx11-xcb1",
    ]

    optional_deps = [
        f"libevent-2.1-7{'t64' if t64 else ''}",
        "libgstreamer-plugins-bad1.0-0",
        "libflite1",
        "libavif16"
    ]

    deps = base_deps + optional_deps

    if os.environ.get("FRAPPE_CLOUD_SITE") or "frappecloud" in frappe.utils.get_url():
        click.secho("Detected Frappe Cloud environment. Skipping system-level installs.", fg="yellow")
        return

    try:
        click.echo("Running: sudo apt-get update and install...")
        subprocess.check_call(["sudo", "apt-get", "update", "-y"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y"] + deps)
        click.echo("System dependencies installed.")
    except subprocess.CalledProcessError as e:
        click.secho(f"apt-get install failed: {e}", fg="red")

def get_bench_python_executable():
    """Return the python executable from current bench environment."""
    bench_path = frappe.utils.get_bench_path()
    return Path(bench_path) / "env" / "bin" / "python3"

def install_playwright_browsers():
    """Run playwright install to download browsers."""
    bench_python = get_bench_python_executable()
    click.echo("Installing Playwright browsers (Chromium, Firefox, WebKit)...")
    try:
        subprocess.check_call([str(bench_python), "-m", "playwright", "install"])
        click.secho("Playwright browsers installed successfully.", fg="green")
    except subprocess.CalledProcessError as e:
        click.secho(f"Browser installation failed: {e}", fg="red")
        raise

def install_playwright_deps():
    """Optionally attempt to run playwright install-deps for system dependencies."""
    bench_python = get_bench_python_executable()
    click.echo("Installing system dependencies via playwright install-deps...")
    try:
        subprocess.check_call([str(bench_python), "-m", "playwright", "install-deps"])
        click.secho("Playwright system dependencies installed.", fg="green")
    except subprocess.CalledProcessError as e:
        click.secho(f"playwright install-deps failed or not permitted: {e}", fg="yellow")
        # This can be optional, as environment might restrict this command
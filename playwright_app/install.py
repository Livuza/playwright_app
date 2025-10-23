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
        install_playwright_browsers()
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
    click.echo("Installing Playwright system dependencies...")

    # Detect Ubuntu version
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

    # Detect if running on Frappe Cloud
    if os.environ.get("FRAPPE_CLOUD_SITE") or "frappecloud" in frappe.utils.get_url():
        click.secho("☁️ Detected Frappe Cloud environment. Skipping system-level installations.", fg="yellow")
        click.secho("Playwright dependencies will only be installed locally or on VM environments.", fg="yellow")
        return

    # Try playwright install-deps first
    try:
        click.echo("Running: sudo playwright install-deps")
        subprocess.check_call(["sudo", "playwright", "install-deps"])
        click.echo("System dependencies installed using playwright install-deps.")
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        click.secho("playwright install-deps not found or failed. Falling back to apt-get...", fg="yellow")

    try:
        click.echo("Installing required libraries via apt-get...")
        subprocess.check_call(["sudo", "apt-get", "update", "-y"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y"] + deps)
        click.echo("All required system libraries installed successfully.")
    except subprocess.CalledProcessError as e:
        click.secho(f"apt-get installation failed: {e}", fg="red")


def get_bench_python_executable():
    """Returns the Python interpreter path from the current bench environment."""
    bench_path = frappe.utils.get_bench_path()
    return Path(bench_path) / "env" / "bin" / "python3"


def install_playwright_browsers():
    """Install Chromium, Firefox, and WebKit browsers, except on Frappe Cloud."""
    bench_python = get_bench_python_executable()

    # Detect Frappe Cloud and skip
    if os.environ.get("FRAPPE_CLOUD_SITE") or "frappecloud" in frappe.utils.get_url():
        click.secho("Detected Frappe Cloud environment.", fg="yellow")
        click.secho("Skipping browser installation — Frappe Cloud restricts browser binaries.", fg="yellow")
        click.secho("You can still run Playwright tests on local or private servers.", fg="yellow")
        return

    click.echo("Installing Playwright browsers (Chromium, Firefox, WebKit)...")

    try:
        subprocess.check_call([str(bench_python), "-m", "playwright", "install"])
        click.echo("Playwright browsers installed successfully.")
    except subprocess.CalledProcessError as e:
        click.secho(f"Browser installation failed: {e}", fg="red")
        raise

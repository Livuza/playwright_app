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
    """Install system dependencies via playwright or apt-get."""
    click.echo("Installing Playwright system dependencies...")

    deps = [
        "libatk1.0-0", "libatk-bridge2.0-0", "libxkbcommon0",
        "libatspi2.0-0", "libxcomposite1", "libxdamage1",
        "libxfixes3", "libxrandr2", "libgbm1", "libasound2", "libx11-xcb1"
    ]

    # Try playwright install-deps first
    try:
        click.echo("Running: sudo playwright install-deps")
        subprocess.check_call(["sudo", "playwright", "install-deps"])
        click.echo("System dependencies installed using playwright install-deps.")
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        click.secho("playwright install-deps failed or not available. Falling back to apt-get...", fg="yellow")

    # Fallback: install manually via apt-get
    try:
        click.echo("Installing required libraries via apt-get...")
        subprocess.check_call(["sudo", "apt-get", "update", "-y"])
        subprocess.check_call(["sudo", "apt-get", "install", "-y"] + deps)
        click.echo("All required system libraries installed successfully.")
    except subprocess.CalledProcessError as e:
        click.secho(f"apt-get installation failed: {e}", fg="red")
        raise


def get_bench_python_executable():
    """Returns the Python interpreter path from the current bench environment."""
    bench_path = frappe.utils.get_bench_path()
    return Path(bench_path) / "env" / "bin" / "python3"


def install_playwright_browsers():
    """Install Chromium, Firefox, and WebKit browsers."""
    bench_python = get_bench_python_executable()
    click.echo("Installing Playwright browsers (Chromium, Firefox, WebKit)...")

    try:
        subprocess.check_call([str(bench_python), "-m", "playwright", "install"])
        click.echo("Playwright browsers installed successfully.")
    except subprocess.CalledProcessError as e:
        click.secho(f"Browser installation failed: {e}", fg="red")
        raise

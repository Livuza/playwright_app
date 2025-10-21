import frappe
import sys
import subprocess
import click
import os
from pathlib import Path

def after_install():
    """Main installation hook executed after the app is installed."""
    click.echo("Starting Playwright and Chromium setup...")

    try:
        install_python_deps()
        install_playwright_package()
        install_system_deps()
        install_playwright_browsers()
        click.secho("Playwright and Chromium setup completed successfully.", fg="green")

    except Exception as e:
        frappe.log_error(title="Playwright Setup Error", message=str(e))
        click.secho(f"Playwright setup failed: {e}", fg="red")

def install_python_deps():
    """Install Playwright Python dependencies."""
    click.echo("Installing Playwright Python dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright==1.55.0"])
    click.echo("Python dependencies installed.")

def install_system_deps():
    """Attempt to install system libraries required by Chromium."""
    deps = [
        "libatk1.0-0", "libatk-bridge2.0-0", "libatspi2.0-0",
        "libxcomposite1", "libxdamage1", "libxfixes3",
        "libxrandr2", "libgbm1", "libxkbcommon0",
        "libasound2", "libx11-xcb1"
    ]

    click.echo("Installing system dependencies for Chromium...")

    # Check if we have root privileges
    if os.geteuid() != 0:
        click.secho(
            "⚠️ Skipping system dependency installation (no root privileges).\n"
            "If running on Frappe Cloud, please contact support to execute:\n"
            "    sudo playwright install-deps\n",
            fg="yellow",
            bold=True
        )
        return

    # Try installing dependencies silently
    try:
        subprocess.check_call(["apt-get", "update", "-y"])
        subprocess.check_call(["apt-get", "install", "-y"] + deps)
        click.echo("System dependencies installed.")
    except Exception as e:
        click.secho(f"Failed to install system dependencies: {e}", fg="red")

def get_bench_python_executable():
    """Get Python path in the current bench environment."""
    bench_path = frappe.utils.get_bench_path()
    return Path(bench_path) / "env" / "bin" / "python3"

def install_playwright_package():
    """Ensure Playwright is installed."""
    try:
        import playwright
        click.echo("Playwright Python package already installed.")
    except ImportError:
        click.echo("Installing Playwright package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])

def install_playwright_browsers():
    """Install Chromium and related browsers."""
    bench_python = get_bench_python_executable()
    click.echo(f"Installing Playwright browsers using: {bench_python}")

    try:
        subprocess.check_call([str(bench_python), "-m", "playwright", "install"])
        click.echo("Chromium and other browsers installed successfully.")
    except subprocess.CalledProcessError as e:
        click.secho(f"Browser installation failed: {e}", fg="red")
        raise

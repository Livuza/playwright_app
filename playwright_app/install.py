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
        install_playwright_browsers()
        click.echo("Playwright and Chromium setup completed successfully.")
        
        # Critical reminder for the system dependencies issue
        click.secho(
            "\n*** ATTENTION FOR CLOUD HOSTING ***\n"
            "The browser binaries are installed, but the host system may still be "
            "missing external dependencies (e.g., libx11-xcb1). If tests fail, "
            "you MUST contact Frappe Cloud Support and ask them to run:\n"
            "  $ sudo playwright install-deps\n",
            fg="yellow",
            bold=True
        )

    except Exception as e:
        frappe.log_error(title="Playwright Setup Error", message=str(e))
        click.secho(f"Playwright setup failed: {e}", fg="red")

def install_python_deps():
    """Install Playwright and its Python dependencies."""
    click.echo("Installing Playwright and dependencies...")
    subprocess.check_call(["pip", "install", "playwright==1.55.0"])

    # Install system dependencies if available
    deps = [
        "libatk1.0-0", "libatk-bridge2.0-0", "libxkbcommon0",
        "libatspi2.0-0", "libxcomposite1", "libxdamage1",
        "libxfixes3", "libxrandr2", "libgbm1", "libasound2", "libx11-xcb1"
    ]
    subprocess.call(["apt-get", "update", "-y"])
    subprocess.call(["apt-get", "install", "-y"] + deps, stderr=subprocess.DEVNULL)
    click.echo("Python & system dependencies installed.")

def get_bench_python_executable():
    """Returns the path to the Python interpreter within the bench environment."""
    # Get the root path of the bench environment
    bench_path = frappe.utils.get_bench_path()
    # Path is typically: [bench_path]/env/bin/python3
    return Path(bench_path) / "env" / "bin" / "python3"


def install_playwright_package():
    """Install Playwright via pip if not already installed."""
    try:
        import playwright
        click.echo("Playwright Python package already installed.")
    except ImportError:
        click.echo("Installing Playwright Python package...")
        # Use sys.executable as it points to the current environment's python
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])


def install_playwright_browsers():
    """Run the official 'playwright install' command using the bench's Python executable."""
    bench_python = get_bench_python_executable()
    
    click.echo(f"Running official Playwright browser installation using: {bench_python}")
    
    try:
        # Command: /path/to/bench/env/bin/python3 -m playwright install
        subprocess.check_call([str(bench_python), "-m", "playwright", "install"])
        click.echo("Chromium and other browsers successfully installed.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Error executing playwright install command: {e}", fg="red")
        raise
import os
import sys
import platform
import subprocess
import zipfile
import shutil
from pathlib import Path
import requests
import click
import frappe


def after_install():
    """Main installation hook."""
    click.echo("Installing Playwright and Chromium dependencies...")

    try:
        install_playwright()
        setup_chromium()
        click.echo("Playwright and Chromium setup completed successfully.")
    except Exception as e:
        frappe.log_error(title="Playwright Setup Error", message=str(e))
        click.secho(f"Playwright setup failed: {e}", fg="red")


def install_playwright():
    """Install Playwright via pip if not already installed."""
    try:
        import playwright  # noqa
        click.echo("Playwright already installed.")
    except ImportError:
        click.echo("Installing Playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright==1.55.0"])

    # Try to run playwright install via Python API (safe for restricted environments)
    try:
        from playwright.__main__ import main
        main(["install", "chromium"])
        click.echo("Chromium browser installed via Playwright.")
    except Exception:
        click.echo("Could not install Chromium via Playwright. Attempting manual download...")
        setup_chromium()


def setup_chromium():
    """Find or download Chromium manually if not present."""
    bench_path = frappe.utils.get_bench_path()
    chromium_dir = os.path.join(bench_path, "chromium")
    os.makedirs(chromium_dir, exist_ok=True)

    exec_path = Path(chromium_dir) / "chrome-headless-shell"
    if exec_path.exists():
        click.echo(f"Chromium already exists at {exec_path}")
        return

    url = get_chromium_download_url()
    zip_path = os.path.join(chromium_dir, "chromium.zip")

    click.echo(f"Downloading Chromium from {url} ...")
    headers = {"User-Agent": "Wget/1.21.1"}
    with requests.get(url, stream=True, timeout=(10, 60), headers=headers) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with click.progressbar(length=total, label="Downloading Chromium") as bar, open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
                bar.update(len(chunk))

    click.echo("Extracting Chromium...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(chromium_dir)
    os.remove(zip_path)

    # Locate and move executable
    for root, _, files in os.walk(chromium_dir):
        for file in files:
            if "chrome-headless-shell" in file or "headless_shell" in file:
                shutil.move(os.path.join(root, file), exec_path)
                break

    if not os.access(exec_path, os.X_OK):
        os.chmod(exec_path, 0o755)

    click.echo(f"Chromium ready at: {exec_path}")


def get_chromium_download_url():
    """Return platform-appropriate Chromium URL."""
    base_url = "https://storage.googleapis.com/chrome-for-testing-public"
    version = "133.0.6943.35"
    system = platform.system().lower()
    arch = platform.machine().lower()

    if system == "linux":
        return f"{base_url}/{version}/linux64/chrome-headless-shell-linux64.zip"
    elif system == "darwin":
        if arch == "arm64":
            return f"{base_url}/{version}/mac-arm64/chrome-headless-shell-mac-arm64.zip"
        else:
            return f"{base_url}/{version}/mac-x64/chrome-headless-shell-mac-x64.zip"
    elif system == "windows":
        return f"{base_url}/{version}/win64/chrome-headless-shell-win64.zip"
    else:
        raise RuntimeError(f"Unsupported platform: {system}-{arch}")

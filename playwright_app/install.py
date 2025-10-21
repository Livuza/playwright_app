import os
import platform
import shutil
import zipfile
import tempfile
import requests
import frappe
from pathlib import Path
import click
import subprocess

def after_install():
    """Install all Playwright dependencies and ensure Chromium is available."""

    try:
        install_python_deps()
        setup_chromium_for_playwright()
        click.echo("Playwright environment ready.")
    except Exception as e:
        click.echo(f"Playwright setup failed: {e}")
        frappe.log_error(f"Playwright setup failed: {e}")


def install_python_deps():
    """Install Playwright and its Python dependencies."""
    click.echo("Installing Playwright and dependencies...")
    subprocess.check_call(["pip", "install", "playwright==1.55.0"])

    # Install system dependencies if available
    deps = [
        "libatk1.0-0", "libatk-bridge2.0-0", "libxkbcommon0",
        "libatspi2.0-0", "libxcomposite1", "libxdamage1",
        "libxfixes3", "libxrandr2", "libgbm1", "libasound2"
    ]
    subprocess.call(["apt-get", "update", "-y"])
    subprocess.call(["apt-get", "install", "-y"] + deps, stderr=subprocess.DEVNULL)
    click.echo("Python & system dependencies installed.")


def setup_chromium_for_playwright():
    """Automatically download Chromium if not found."""
    bench_path = frappe.utils.get_bench_path()
    chromium_dir = os.path.join(bench_path, "chromium")
    os.makedirs(chromium_dir, exist_ok=True)

    # Check if Chromium already exists
    chromium_exec = find_chromium_executable(chromium_dir)
    if chromium_exec and os.path.exists(chromium_exec):
        click.echo(f"Chromium already present at: {chromium_exec}")
        return chromium_exec

    click.echo("Chromium not found, downloading...")
    url = get_chromium_download_url()
    zip_path = os.path.join(tempfile.gettempdir(), os.path.basename(url))

    with requests.get(url, stream=True, headers={"User-Agent": "Wget/1.21.1"}) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        bar = click.progressbar(length=total, label="Downloading Chromium")
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
                bar.update(len(chunk))

    click.echo("Extracting Chromium...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(chromium_dir)
    os.remove(zip_path)

    # Ensure executable is available
    exec_path = find_chromium_executable(chromium_dir)
    if not exec_path or not os.path.exists(exec_path):
        raise RuntimeError("Chromium executable not found after extraction.")

    os.chmod(exec_path, 0o755)
    click.echo(f"Chromium ready at: {exec_path}")

    return exec_path


def find_chromium_executable(chromium_dir):
    """Locate Chromium binary depending on platform."""
    system = platform.system().lower()
    exec_map = {
        "linux": ["chrome-linux/chrome", "chromium/chrome", "headless_shell"],
        "darwin": ["chrome-mac/Chromium.app/Contents/MacOS/Chromium"],
        "windows": ["chrome-win/chrome.exe"],
    }

    for subpath in exec_map.get(system, []):
        full_path = os.path.join(chromium_dir, subpath)
        if os.path.exists(full_path):
            return full_path

    return None


def get_chromium_download_url():
    """Return platform-appropriate Chromium download URL."""
    system = platform.system().lower()
    arch = platform.machine().lower()

    # Default to Chromium 133 (matches Playwright 1.55.0)
    version = "133.0.6943.35"
    base = "https://storage.googleapis.com/chrome-for-testing-public"

    if system == "linux" and arch in ["x86_64", "amd64"]:
        return f"{base}/{version}/linux64/chrome-headless-shell-linux64.zip"
    elif system == "darwin" and arch == "arm64":
        return f"{base}/{version}/mac-arm64/chrome-headless-shell-mac-arm64.zip"
    elif system == "darwin":
        return f"{base}/{version}/mac-x64/chrome-headless-shell-mac-x64.zip"
    elif system == "windows":
        return f"{base}/{version}/win64/chrome-headless-shell-win64.zip"
    else:
        raise RuntimeError(f"Unsupported system: {system} {arch}")

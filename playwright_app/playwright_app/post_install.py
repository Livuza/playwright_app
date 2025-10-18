import subprocess

def after_install():
    subprocess.run(["playwright", "install", "chromium"], check=True)
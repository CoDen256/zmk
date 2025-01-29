import os
import shutil
import time
import zipfile

import requests


# Define the folder to watch and the target disk

token = ""

def get_run():
    print(f"Getting runs")
    return requests.get("https://api.github.com/repos/coden256/zmk-config/actions/workflows/build.yml/runs?per_page=1&branch=master&event=push&status=success").json()['workflow_runs'][0]['id']

def get_artifact(run):
    print(f"Getting artifact for run {run}")
    return requests.get(f"https://api.github.com/repos/CoDen256/zmk-config/actions/runs/{run}/artifacts?per_page=1").json()['artifacts'][0]['archive_download_url']

def download(url, target):
    print(f"Downloading {url} to {target}")
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    with open(target+"/firmware.zip", mode="wb") as file:
        file.write(r.content)

def download_latest_artifact(target):
    download(get_artifact(get_run()), target)


def wait_for_file(folder, extension):
    """Poll the folder for a file with the given extension."""
    print(f"Polling for {extension} in {folder}")
    while True:
        for filename in os.listdir(folder):
            if filename.endswith(extension):
                return filename
        time.sleep(1)  # Poll every second

def wait_for_device(disk):
    """Wait for the device (disk) to become available."""
    while True:
        if os.path.exists(disk):
            return
        time.sleep(1)  # Poll every second

def extract_and_copy(zip_path, file_substr, target_disk):
    """Extract the file containing the given substring from the zip file and copy it to the target disk."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file_substr in file:
                print(f"Extracting {file} to {target_disk}")
                target_path = os.path.join(target_disk, file)
                with zip_ref.open(file) as source, open(target_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                print(f"Copied {file} to {target_path}")
                return

def copy(path, target_disk):
    name = os.path.basename(path)
    target_path = os.path.join(target_disk, name)
    print(f"Copying {path} to {target_path}")
    shutil.copy(path, target_path)


def run(watched_folder, target_disk):
    # Step 1: Wait for the first device connection
    print(f"[deployer-{target_disk}] Waiting for device connection at {target_disk}...")
    wait_for_device(target_disk)

    # Step 2: Download latest artifact
    # download_latest_artifact(watched_folder)

    # Step 3: Check for a .zip file in the watched folder
    file = wait_for_file(watched_folder, '.uf2')
    file_path = os.path.join(watched_folder, file)
    print(f"[deployer-{target_disk}] Found .uf2: {file_path}")


    # Copy the file to the device
    copy(file_path,  target_disk)
    print(f"[deployer-{target_disk}] Done")



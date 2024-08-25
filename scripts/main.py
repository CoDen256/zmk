import importlib
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import builder
import drawer
import deployer
import keycombiner
import updater
import modder


def check_file_update(name, file_path, script, *args):
    print(f"[{name}] started")
    try:
        # Check the current modification time of the file
        last_modified_time = os.path.getmtime(file_path)
    except FileNotFoundError:
        # print(f"The file {file_path} does not exist.")
        last_modified_time = None
    while True:
        try:
            try:
                # Check the current modification time of the file
                current_modified_time = os.path.getmtime(file_path)
            except FileNotFoundError:
                # print(f"The file {file_path} does not exist.")
                current_modified_time = last_modified_time = None
            # print(f"{name} {last_modified_time} -> {current_modified_time}")
            # If the modification time has changed, run the PowerShell script
            if current_modified_time and current_modified_time != last_modified_time:
                print(f"[{name}] File {file_path} has been updated")
                script(*args)
                # Update the last modification time
                last_modified_time = current_modified_time

                # print("Sleeping...")
            # Wait for 10 seconds before checking again
            time.sleep(5)
        except Exception as e:
            print(f"[{name}] failed ", e)
            time.sleep(30)


def reload(module, file):
    name = module.__name__
    print(f"[reloader-{name}] reloading {module.__file__}")
    importlib.reload(module)
    print(f"[reloader-{name}] done")
    Path(file).touch()

def run(name, file_path, script, *args):

    threading.Thread(target=check_file_update,
                     args=(f"reloader-{name}", script.__file__, reload, script, file_path)).start()

    threading.Thread(target=check_file_update,
                     args=(name, file_path, script.run, *args)).start()


def rund(*args):
    pass


def run_shell(script):
    subprocess.call(script, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    time.sleep(12)


if __name__ == "__main__":
    # file_path = "../config/glove80.keymap"
    # dir = "/"
    # check_file_update(file_path, dir)
    run_shell("C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe")
    base = "C:\\dev\\zmk-config"
    run("builder",
        f"{base}\\config\\glove80.keymap",
        builder,
        base,
        )
    run("drawer",
        f"{base}\\glove80.uf2",
        drawer,
        base,
        )
    run(
        "deployer-D",
        'D:\\',
        deployer,
        base,
        'D:\\',
    )

    run(
        "deployer-2",
        'E:\\',
        deployer,
        base,
        'E:\\',
    )

    run(
        "keycombiner",
        f"{base}\\shortcuts\\keymap.xml",
        keycombiner,
        f"{base}\\shortcuts\\keymap.xml",
        f"{base}\\shortcuts\\keymap.csv",
    )

    run(
        "keycombiner-updater",
        f"{base}\\shortcuts\\keymap.csv",
        updater,
        f"{base}\\shortcuts\\keymap.csv",
        f"{base}\\scripts\\pass",
        33922
    )

    run(
        "modder",
        f"{base}\\shortcuts\\mods.yaml",
        modder,
        f"{base}\\shortcuts\\mods.yaml",
        f"{base}\\config\\glove80.keymap",
    )

    # Keep the main thread running
    input()

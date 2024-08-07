import os
import subprocess
import sys
import threading
import time
import builder
import drawer
import deployer
import keycombiner

def check_file_update(name, file_path, script, *args):
    print(f"[{name}] started")
    last_modified_time = None
    try:
        while True:
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


def run(name, file_path, script, *args):
    threading.Thread(target=check_file_update,
                     args=(name, file_path, script, *args)).start()
def rund(*args):
    pass
def run_shell(script):
    subprocess.call(script, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    time.sleep(12)

if __name__ == "__main__":
    # file_path = "../config/glove80.keymap"
    # dir = "/"
    # check_file_update(file_path, dir)
    # run_shell("C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe")
    base = "C:\\dev\\zmk-config"
    rund("builder",
        f"{base}\\config\\glove80.keymap",
        builder.build,
        base,
        )
    rund("drawer",
        f"{base}\\glove80.uf2",
        drawer.draw,
        base,
        )
    rund(
        "deployer-1",
        'D:\\',
        deployer.deploy,
        base,
        'D:\\',
    )

    rund(
        "deployer-2",
        'E:\\',
        deployer.deploy,
        base,
        'E:\\',
    )

    run(
        "keycombiner",
        f"{base}\\shortcuts\\keymap.xml",
        keycombiner.transform,
        f"{base}\\shortcuts\\keymap.xml",
        f"{base}\\shortcuts\\keymap.csv",
    )

        # Keep the main thread running
    input()

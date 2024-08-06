import os
import threading
import time
import autobuilder

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
            print(f"{name} {last_modified_time} -> {current_modified_time}")
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


if __name__ == "__main__":
    # file_path = "../config/glove80.keymap"
    # dir = "/"
    # check_file_update(file_path, dir)
    run()
        # Keep the main thread running
    while True:
        time.sleep(5)

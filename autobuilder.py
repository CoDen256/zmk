import os
import time
import subprocess
import sys

def run_powershell_script(script_path):
    # Start the PowerShell process
    process = subprocess.Popen(
        ['docker', 'run', '--rm', '-v ${PWD}:/config', '-e BRANCH="main"', '-e UID="1000"', '-e GID="1000"', 'glove80'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print("Opened process")

    try:
        # Read the process output in real-time
        for c in iter(lambda: process.stdout.read(1), ""):
            sys.stdout.write(c)
        
        # Capture any errors
        error = process.stderr.read()
        if error:
            print(f"Error: {error.strip()}")
    except KeyboardInterrupt:
        # Handle the user interrupt (Ctrl+C)
        process.terminate()
        print("\nProcess terminated by user")
    finally:
        process.stdout.close()
        process.stderr.close()
        process.wait()

def check_file_update(file_path, powershell_script):
    last_modified_time = None

    while True:
        print("Checking file...")
        try:
            # Check the current modification time of the file
            current_modified_time = os.path.getmtime(file_path)
        except FileNotFoundError:
            print(f"The file {file_path} does not exist.")
            return

        # If the modification time has changed, run the PowerShell script
        if current_modified_time != last_modified_time:
            print(f"File {file_path} has been updated. Executing PowerShell script {powershell_script}...")
            run_powershell_script(powershell_script)
            # Update the last modification time
            last_modified_time = current_modified_time

        print("Waiting...")
        # Wait for 10 seconds before checking again
        time.sleep(10)

if __name__ == "__main__":
    file_path = "config/glove80.keymap"
    powershell_script = "./build.ps1"
    check_file_update(file_path, powershell_script)

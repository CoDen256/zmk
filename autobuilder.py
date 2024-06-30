import os
import time
import subprocess
import sys
import docker
import time

def run_powershell_script(dir):
    # Start the PowerShell process
    cmd = f'docker run --rm -v "{dir}:/config" -e BRANCH="main" -e UID="1000" -e GID="1000" glove80'
    print(cmd)
    subprocess.call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)

def run(dir):
    client = docker.from_env()
    container = client.containers.run("glove80",  detach=True, auto_remove=True, 
                                      volumes=[f"{dir}:/config"],
                                      environment={
                                          "BRANCH": "main",
                                          "UID": "1000",
                                          "GID": "1000",
                                      }
                                      )

    logs = []
    # you can even stream your output like this:
    for line in container.logs(stream=True):
        log = line.decode("utf-8")
        print(log.strip())
        logs.append(log.strip())
    result = container.wait()
    if (int(result['StatusCode'])) != 0:
        error = list(filter(lambda x: x.startswith("devicetree error"), logs))
        if not error:
            error = "Unknown error, see logs"
        else: 
            error = error[0]
        print(f"\n\033[1;91m{error}\033[0m")
    else:
        print("\n\033[1;92mSUCCESS:\033[0m glove80.uf2 is built!")
        subprocess.call("python ./draw/drawer.py")

def check_file_update(file_path, dir):
    last_modified_time = None

    while True:
        try:
            # Check the current modification time of the file
            current_modified_time = os.path.getmtime(file_path)
        except FileNotFoundError:
            print(f"The file {file_path} does not exist.")
            return

        # If the modification time has changed, run the PowerShell script
        if current_modified_time != last_modified_time:
            print(f"File {file_path} has been updated. Executing docker glove80 image...")
            run(dir)
            # Update the last modification time
            last_modified_time = current_modified_time

            print("Sleeping...")
        # Wait for 10 seconds before checking again
        time.sleep(5)

if __name__ == "__main__":
    file_path = "config/glove80.keymap"
    dir = "C:\\dev\\zmk-config"
    check_file_update(file_path, dir)

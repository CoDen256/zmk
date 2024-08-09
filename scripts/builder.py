import docker


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



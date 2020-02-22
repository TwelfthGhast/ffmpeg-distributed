import os
import hashlib
import subprocess
from time import sleep
from global_var import NFS_ROOT, POLL_DOCKER_INTERVAL

# Check whether any segments to encode
def poll_docker():
    for dirname in os.listdir(NFS_ROOT):
        if dirname[:1] == ".":
            continue
        full_path = os.path.join(NFS_ROOT, dirname)
        if os.path.isdir(full_path):
            print(full_path)
            for filename in os.listdir(full_path):
                if filename[-4:] == ".log":
                    continue
                elif filename[:9] != "processed" and not os.path.isfile(os.path.join(full_path, f"processed-{filename}")):
                    print(f"[DOCKER] Setting up docker (one-shot) service to process {filename}")
                    print(filename[:9])
                    split_command = f"docker service create \
                        --restart-condition on-failure \
                        --name ffmpeg-{hashlib.md5(filename.encode('utf-8')).hexdigest()} \
                        --mount type=bind,source={full_path},target=/temp \
                        jrottenberg/ffmpeg:4.1-alpine \
                        -i /temp/{filename} \
                        -c:v libx265 -crf 20 -preset veryslow\
                        /temp/processed-{filename}"
                    # capture_output=True, encoding="utf-8"
                    subprocess.run(split_command.split())
    sleep(POLL_DOCKER_INTERVAL)
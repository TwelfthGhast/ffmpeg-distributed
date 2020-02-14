#!/usr/bin/python3.7

# python 3.7 needed for subprocess arguments
# added shebang as updating to python 3.6 breaks some install programs on dev environment

import os
import subprocess
from time import sleep
from sys import stderr
import shutil
import threading
import hashlib
import stat

NEW_DIRECTORY = "new"
PROCESS_DIRECTORY = "processing"
NFS_ROOT = "/mnt/nfs-client"
# poll interval in seconds
POLL_NEW_INTERVAL = 5
POLL_DOCKER_INTERVAL = 2

def check_file_size(filename):
    full_path = os.path.join(NEW_DIRECTORY, filename)

    # Ensure file_size remains consistent across short time period
    # File may be copying to the "new" directory
    file_size_one = os.stat(full_path).st_size
    sleep(1)
    file_size_two = os.stat(full_path).st_size

    static_file = (file_size_one == file_size_two)
        
    # If file remains constant in folder
    # Process and split into keyframe fragments
    if static_file:
        shutil.move(full_path, os.path.join(PROCESS_DIRECTORY, filename))
        split_file(filename)


def poll_new():
    for filename in os.listdir(NEW_DIRECTORY):
        full_path = os.path.join(NEW_DIRECTORY, filename)
        if os.path.isfile(full_path):
            x = threading.Thread(target=check_file_size, args=(filename,))
            x.start()
    sleep(POLL_NEW_INTERVAL)


def split_file(filename):
    print(f"[NEW FILE] Attempting to split '{filename}'")
    file_path = os.path.join(PROCESS_DIRECTORY, filename)

    if os.path.isfile(file_path):
        # Split file into NFS drive
        split_path = os.path.join(NFS_ROOT, filename)
        
        # Check if path to split files already exists
        if not os.path.isdir(split_path):
            # Create new folder and chmod 777 it
            os.mkdir(split_path)
            os.chmod(split_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

            new_file_path = os.path.join(split_path, f"%d-{filename}")
            split_command = f"ffmpeg -i {file_path} -acodec copy -f segment -vcodec copy -reset_timestamps 1 -map 0 {new_file_path}"
            output = subprocess.run(split_command.split(), capture_output=True, encoding="utf-8")

            # Save debug information
            with open(os.path.join(split_path, "stdout.log"), "w") as f:
                f.write(output.stdout)
                f.close()
            with open(os.path.join(split_path, "stderr.log"), "w") as f:
                f.write(output.stderr)
                f.close()
            
            # If ffmpeg did not split files successfully
            if output.returncode != 0:
                print(f"{filename} was not split successfully. Please check '{split_path}' for additional information")
                shutil.move(file_path, os.path.join(split_path, filename))
            else:
                os.remove(file_path)

        # Not sure how to handle this but files has already been processed once
        else:
            print("File already processing...")
            pass
    else:
        print(f"Unexpected file '{filename}' was not located in processing directory '{PROCESS_DIRECTORY}'", file=stderr)


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
                    sleep(1)


    sleep(POLL_DOCKER_INTERVAL)


# Wake any inactive processing nodes
def wol_nodes():
    pass


def check_folders():
    # Create folders if it doesn't exist
    if not os.path.isdir(NEW_DIRECTORY):
        os.mkdir(NEW_DIRECTORY)
    if not os.path.isdir(PROCESS_DIRECTORY):
        os.mkdir(PROCESS_DIRECTORY)
    if not os.path.isdir(NFS_ROOT):
        print("Could not find NFS directory.", file=stderr)
        exit(1)


if __name__ == "__main__":
    check_folders()
    while True:
        poll_new()
        poll_docker()
        



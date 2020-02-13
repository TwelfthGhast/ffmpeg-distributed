import os
import subprocess
from time import sleep
from sys import stderr
import shutil

NEW_DIRECTORY = "new"
PROCESS_DIRECTORY = "processing"
NFS_ROOT = "/mnt/nfs-client"
# poll interval in seconds
POLL_INTERVAL = 1

def poll_new():


    for filename in os.listdir(NEW_DIRECTORY):
        full_path = os.path.join(NEW_DIRECTORY, filename)

        # Ensure file_size remains consistent across short time period
        # File may be copying to the "new" directory
        file_size_one = os.stat(full_path).st_size
        sleep(0.1)
        file_size_two = os.stat(full_path).st_size

        static_file = (file_size_one == file_size_two)
        
        # If file remains constant in folder
        # Process and split into keyframe fragments
        if static_file:
            shutil.move(full_path, os.path.join(PROCESS_DIRECTORY, filename))
            split_file(filename)

def split_file(filename):
    file_path = os.path.join(PROCESS_DIRECTORY, filename)

    if os.path.isfile(file_path):
        # Split file into NFS drive
        split_path = os.path.join(NFS_ROOT, filename)
        
        # Check if path to split files already exists
        if not os.path.isdir(split_path):
            os.mkdir(split_path)
            new_file_path = os.path.join(split_path, f"%d-{filename}")
            split_command = f"ffmpeg -i {file_path} -acodec copy -f segment -vcodec copy -reset_timestamps 1 -map 0 {new_file_path}"
            output = subprocess.run(split_command.split(), capture_output=True, encoding="utf-8")

            # Save debug information
            with open(os.path.join(split_path, "log.stdout"), "w") as f:
                f.write(output.stdout)
                f.close()
            with open(os.path.join(split_path, "log.stderr"), "w") as f:
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

def check_folders():
    # Create folders if it doesn't exist
    if not os.path.isdir(NEW_DIRECTORY):
        os.mkdir(NEW_DIRECTORY)
    if not os.path.isdir(PROCESS_DIRECTORY):
        os.mkdir(PROCESS_DIRECTORY)
    if not os.path.isdir(NFS_ROOT):
        print("Could not find NFS directory.", file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    check_folders()
    while True:
        poll_new()
        sleep(POLL_INTERVAL)



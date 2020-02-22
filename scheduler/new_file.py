import os
from time import sleep
import shutil
import threading
import subprocess
import stat
from sys import stderr
from global_var import NEW_DIRECTORY, PROCESS_DIRECTORY, NFS_ROOT, POLL_NEW_INTERVAL

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
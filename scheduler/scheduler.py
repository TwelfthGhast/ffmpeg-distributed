#!/usr/bin/python3.7

# python 3.7 needed for subprocess arguments
# added shebang as updating to python 3.6 breaks some install programs on dev environment

import os

from time import sleep
from sys import stderr
import shutil
import threading
from encode_file import poll_docker
from new_file import poll_new
from nodes import initialise_nodes
from global_var import NFS_ROOT, PROCESS_DIRECTORY, NEW_DIRECTORY
from encode_file import poll_docker
from new_file import poll_new
from nodes import initialise_nodes

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
    initialise_nodes()
    while True:
        poll_new()
        poll_docker()
        



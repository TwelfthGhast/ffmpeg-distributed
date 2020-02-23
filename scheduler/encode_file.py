import os
import hashlib
import subprocess
import threading
from time import sleep
from global_var import NFS_ROOT, POLL_DOCKER_INTERVAL, VIDEO_EXTENSIONS, node_list, status_header
from nodes import get_free_node, node_by_hostname

# Generator to do node (folder) traversal through filesystem
def get_unencoded(filepath):
    for dirname in os.listdir(filepath):
        if dirname[:1] == "." or dirname[:9] == "processed":
            continue
        new_path = os.path.join(filepath, dirname)
        if os.path.isdir(new_path):
            yield from get_unencoded(new_path)
        elif new_path.split(".")[-1] in VIDEO_EXTENSIONS and not os.path.isfile(os.path.join(filepath, f"processed-{dirname}")):
            yield new_path


def start_docker_service(filepath, hostname):
    full_path = "/".join(filepath.split("/")[:-1])
    filename = filepath.split("/")[-1]
    service_name = f"ffmpeg-{hashlib.md5(filename.encode('utf-8')).hexdigest()}"
    print(f"{status_header(hostname)}Encoding {filename} with docker service {service_name}")
    split_command = f"docker service create \
                        --restart-condition on-failure \
                        --name {service_name} \
                        --mount type=bind,source={full_path},target=/temp \
                        --constraint node.hostname=={hostname} \
                        jrottenberg/ffmpeg:4.1-alpine \
                        -i /temp/{filename} \
                        -c:v libx265 -crf 20 -preset veryslow\
                        /temp/processed-{filename}"
    subprocess.run(split_command.split(), capture_output=True)
    print(f"{status_header(hostname)}Docker service has converged.")
    node_by_hostname(hostname).update_status()


# Check whether any segments to encode
def poll_docker():
    queue_size = len(node_list) + 5

    gen_files = get_unencoded(NFS_ROOT)
    gen_nodes = get_free_node()

    queue = []
    try:
        while len(queue) < queue_size:
            queue.append(next(gen_files))
        while True:
            # NB: gen_nodes should never trigger StopIteration
            free_hostname = next(gen_nodes)
            x = threading.Thread(target=start_docker_service, args=(queue.pop(0), free_hostname))
            queue.append(next(gen_files))
            x.start()
    # No more files in our generator
    except StopIteration:
        while len(queue) > 0:
            # NB: gen_nodes should never trigger StopIteration
            free_hostname = next(gen_nodes)
            x = threading.Thread(target=start_docker_service, args=(queue.pop(0), free_hostname))
            x.start()

    sleep(POLL_DOCKER_INTERVAL)
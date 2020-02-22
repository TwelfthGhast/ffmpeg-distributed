from wol import send_magic_packet
from global_var import node_list
import subprocess
import json
from time import sleep

def wake_on_lan(mac_addr):
    send_magic_packet(mac_addr)

    
def remote_shutdown():
    pass

  
class DockerNode:
    instances = []
    def __init__(self, mac_addr, hostname):
        self.mac_addr = mac_addr
        self.hostname = hostname
        self.online = False
        self.busy = False
        self.availability = "active"
        self.ip = "0.0.0.0"
        DockerNode.instances.append(self)

    def update_busy(self):
        # Insecure to run pipes
        # Run commands individually
        # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes

        cmd_docker = f"docker node ps {self.hostname}"
        docker_processes = subprocess.run(cmd_docker.split(), capture_output = True)
        cmd_grep_name = "grep ffmpeg"
        grep_temp = subprocess.run(cmd_grep_name.split(), input = docker_processes.stdout, capture_output = True)
        cmd_grep_status = "grep Running"
        grep_list = subprocess.run(cmd_grep_status.split(), input = grep_temp.stdout, capture_output = True)
        cmd_line_count = "wc -l"
        count_lines = subprocess.run(cmd_line_count.split(), input = grep_list.stdout, capture_output = True)
        
        ffmpeg_container_count = int(count_lines.stdout.decode('utf-8').strip())
        self.busy = ffmpeg_container_count > 0

        return ffmpeg_container_count


    def update_status(self):
        cmd_docker = f"docker inspect {self.hostname}"
        docker_inspect = subprocess.run(cmd_docker.split(), capture_output = True)

        docker_info = json.loads(docker_inspect.stdout.decode('utf-8'))

        status = docker_info[0]["Status"]["State"]
        self.availability = docker_info[0]["Spec"]["Availability"]
        self.ip = docker_info[0]["Status"]["Addr"]

        if status == "ready":
            self.online = True
            self.update_busy()
        else: # Down
            self.busy = False
            self.online = False

        

def get_free_node():
    offline_nodes = []
    while True:
        for node in DockerNode.instances:
            node.update_status()
            if node.online and not node.busy:
                return node.hostname
            elif not node.online:
                offline_nodes.append(node)
        for i in range(0, len(offline_nodes)):
            print(f"Waking up worker with hostname '{offline_nodes[i].hostname}'.")
            wake_on_lan(offline_nodes[i].mac_addr)
            tries = 0
            # Wait for up to a minute for worker node to boot and reconnect to swarm
            while tries < 12:
                offline_nodes[i].update_status()
                if offline_nodes[i].online:
                    print(f"Worker with hostname '{offline_nodes[i].hostname}' woke up!")
                    return offline_nodes[i].hostname
                sleep(5)
                tries += 1

def initialise_nodes():
    for mac_addr, hostname in node_list:
        DockerNode(mac_addr, hostname)
    for node in DockerNode.instances:
        print(f"Updating:\t\t{node.mac_addr}\t{node.hostname}")
        node.update_status()
    

        

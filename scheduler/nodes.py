from wol import send_magic_packet
from global_var import node_list
import subprocess

def wake_on_lan(mac_addr):
    send_magic_packet(mac_addr)

class DockerNode:
    instances = []
    def __init__(self, mac_addr, hostname):
        self.mac_addr = mac_addr
        self.hostname = hostname
        self.online = False
        self.availability = "Active"
        DockerNode.instances.append(self)

    def update_status(self):
        # Insecure to run pipes
        # Run commands individually
        # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
        cmd_docker = "docker node ls"
        docker_nodes = subprocess.run(cmd_docker.split(), capture_output = True)
        cmd_grep = f"grep {self.hostname}"
        grep_status = subprocess.run(cmd_grep.split(), input=docker_nodes.stdout, capture_output = True)
        # print(grep_status.stdout)
        cmd_awk_status = ['awk', '{print $3}']
        node_status = subprocess.run(cmd_awk_status, input=grep_status.stdout, capture_output = True)
        cmd_awk_avail = ['awk', '{print $4}']
        node_avail = subprocess.run(cmd_awk_avail, input=grep_status.stdout, capture_output = True)

        status = node_status.stdout.decode('utf-8').strip()
        if status == "Ready":
            self.online = True
        else: # Down
            self.online = False

        self.availability = node_avail.stdout.decode('utf-8').strip()

def initialise_nodes():
    for mac_addr, hostname in node_list:
        DockerNode(mac_addr, hostname)
    for node in DockerNode.instances:
        print(f"Updating:\t\t{node.mac_addr}\t{node.hostname}")
        node.update_status()
    

        

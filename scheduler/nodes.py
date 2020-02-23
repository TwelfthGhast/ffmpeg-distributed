from wol import send_magic_packet
from global_var import node_list, NODE_PENDING_INTERVAL, NODE_UPDATE_INTERVAL, status_header
import subprocess
import json
from time import sleep
from datetime import datetime

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
        self.pending = False
        self.pending_datetime = datetime.now().timestamp()
        self.availability = "active"
        self.ip = "0.0.0.0"
        DockerNode.instances.append(self)

    def update_busy(self):
        initial_status = self.busy
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
        final_status = self.busy
        
        if self.busy:
            self.pending = False
        elif datetime.now().timestamp() - self.pending_datetime > NODE_PENDING_INTERVAL:
            self.pending = False 

        if initial_status == True and final_status == False:
            print(f"{status_header(self.hostname)}No longer busy")

        return ffmpeg_container_count


    def pending_busy(self):
        self.pending = True
        self.pending_datetime = datetime.now().timestamp()


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
            self.pending = False
            self.online = False

        
def get_free_node():
    while True:
        offline_nodes = []
        for node in DockerNode.instances:
            node.update_status()
            if node.online and not node.busy and not node.pending:
                node.pending_busy()
                yield node.hostname
            elif not node.online:
                # Pre-emptively wake nodes as tasks usually come in batches
                wake_on_lan(node.mac_addr)
                offline_nodes.append(node)
        
        # Handle previously offline nodes
        while len(offline_nodes) > 0:
            tries = 0
            # Wait for up to a minute for worker node to boot and reconnect to swarm
            # If dead worker due to very slow startup or hardware failure, ignore and move on
            while tries < 12:
                for i in range(0, len(offline_nodes)):
                    wake_on_lan(offline_nodes[i].mac_addr)
                    offline_nodes[i].update_status()
                    if offline_nodes[i].online:
                        node = offline_nodes.pop(i)
                        node.pending_busy()
                        yield node.hostname
                        tries = 12345
                        break
                sleep(5)
                tries += 1
            # Waited for a long time but these nodes still offline
            # Probably dead or requiring human interaction
            if tries != 12345:
                for node in offline_nodes:
                    print(f"{status_header('ERROR')}Can't wake {node.hostname}")
                    DockerNode.instances.remove(node)
                offline_nodes = []
            
                
                
        # More than sufficient time for any previously scheduled 
        # docker services to start and converge
        wait_start = datetime.now().timestamp()
        print("Waiting on busy nodes to free up...", end='\r', flush=True)
        all_busy = True
        while all_busy:
            sleep(NODE_UPDATE_INTERVAL)
            elapsed_time = int(datetime.now().timestamp() - wait_start)
            print(f"Waiting on busy nodes to free up...\t{elapsed_time} s", end='\r', flush=True)
            for node in DockerNode.instances:
                # if offline
                if not node.online:
                    wake_on_lan(node.mac_addr)
                # if online and no tasks
                elif not node.busy and not node.pending:
                    all_busy = False
                    break


def node_by_hostname(hostname):
    for node in DockerNode.instances:
        if node.hostname == hostname:
            return node


def initialise_nodes():
    for mac_addr, hostname in node_list:
        DockerNode(mac_addr, hostname)
    for node in DockerNode.instances:
        print(f"{status_header('INITIALISATION')}MAC: {node.mac_addr}\tHOSTNAME: {node.hostname}")
        

def poll_node_status():
    while True:
        for node in DockerNode.instances:
            node.update_status()
        sleep(NODE_UPDATE_INTERVAL)
from datetime import datetime

NFS_ROOT = "/mnt/nfs-ffmpeg"
POLL_DOCKER_INTERVAL = 2
NEW_DIRECTORY = "new"
PROCESS_DIRECTORY = "processing"
POLL_NEW_INTERVAL = 5
NODE_PENDING_INTERVAL = 20
NODE_UPDATE_INTERVAL = 1

VIDEO_EXTENSIONS = ["mp4", "mkv"]

node_list = [
    ("C4:34:6B:6E:E8:38", "ghast-node-2"),
    ("C4:34:6B:77:9B:80", "ghast-node-1"),
    ("F8:B1:56:C5:8E:26", "ghast-node-5")
]

def status_header(status):
    return "{:<35}".format(f"[{status} @ {datetime.now().strftime('%H:%M:%S')}]")

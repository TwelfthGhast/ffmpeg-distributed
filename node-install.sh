#!/bin/bash

NFS_IP="192.168.0.150"
DOCKER_WORKER_JOIN_TOKEN="SWMTKN-1-26k9pgeq0twp9cd8xzoa188o0pni1dgpsb18j78vrhzobdkigm-d24afnfa192ferahx0zzmu73i"
# default port for docker 
DOCKER_SWARM_PORT="2377"

# Check for root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add default user (id: 1000) to docker group so don't need sudo to run docker
sudo usermod -aG docker $(getent passwd 1000 | cut -d: -f1)

# Install NFS package
sudo apt-get install nfs-common -y

# Create mount point for NFS
sudo mkdir -p /mnt/nfs-ffmpeg

# save persistent mount in /etc/fstab
echo "$NFS_IP:/mnt/nfs-ffmpeg /mnt/nfs-ffmpeg nfs auto,nofail,noatime,nolock,intr,tcp,actimeo=1800 0 0" | sudo tee -a /etc/fstab

# Add to docker swarm
# sudo needed as changed to user group not effective as no reboot
sudo docker swarm --token $DOCKER_WORKER_JOIN_TOKEN $NFS_IP:$DOCKER_SWARM_IP

# Allow all users to shutdown and reboot without password
echo "ALL ALL=NOPASSWD: /sbin/reboot, /sbin/shutdown, /sbin/poweroff" | sudo tee -a /etc/sudoers

# reboot
sudo reboot

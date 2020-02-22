#!/bin/bash

# Check for root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Update packages
sudo apt-get update
sudo apt-get upgrade

# Install docker using convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add default user (id: 1000) to docker group so don't need sudo to run docker
sudo usermod -aG docker $(getent passwd 1000 | cut -d: -f1)

# Install NFS package
sudo apt-get install nfs-common -y

# Create mount point for NFS
sudo mkdir -p /mnt/nfs-ffmpeg

# Prompt for server IP
# save persistent mount in /etc/fstab
# Add to docker swarm
# sudo needed as changed to user group not effective as no reboot
# reboot

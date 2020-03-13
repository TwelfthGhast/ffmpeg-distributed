#!/bin/bash

# Check for root
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Update packages
sudo apt-get update
sudo apt-get upgrade

# Install wakeonlan
sudo apt-get install wakeonlan -y

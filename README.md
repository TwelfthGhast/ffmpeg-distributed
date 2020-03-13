# ffmpeg-distributed
Distributed processing of videos using docker swarms
Somewhat working - still need to implement searching through nested folders for video files, automatically joining encoded video segments and better error handling. Also need to delete docker services when they are completed

# What is this?

Have high quality video files but not enough disk space? Don't mind using lossy compression? This project aims to use FFMPEG's ability to split videos into keyframe segments to simultaneously encode the same video across multiple physical machines. By default, this uses CPU only and HEVC encoding for the best quality for a given bitrate.

Is this for you?
* You have access to cheap/free machines
* Not overly expensive electricity
* Lots of videos to encode

Otherwise, it may be cheaper to use some online video encoding services which provision cloud services to do the processing instead.

# Deployment

Some steps are still not automated :(

You will need to provision a machine for NFS reasons - docker containers can nicely bind to NFS mounts :) NFS machines should have static IP addresses. By default, this project mounts NFS shares as /mnt/nfs-ffmpeg in manager and worker machines.

You will need to manually install docker on manager machines and initialise the docker swarm.

Scripts have been tested on fresh Ubuntu 18.04 installs.
Make sure you update the `node-install.sh` file with the correct docker swarm worker token and the correct NFS address.

    chmod +x node-install.sh
    ./node-install.sh
    
There may be a bug in which the node has not joined the swarm - in that case you may have to manually join the swarm (though necessary packages should be successfully installed)

You will then need to manually add the hostname and MAC addresses of your nodes to `scheduler/global_var.py` if you wish to take advantage of Wake-on-lan for power saving measures when nodes are inactive. You may also need to update the mount point of the NFS partition.

After you are done, simply run `scheduler/scheduler.py` :) The script will automatically run any files it finds in the NFS directory that requires processing, split it and encode each segment.

You will need to manually rejoin the encoded segments using FFMPEG :(

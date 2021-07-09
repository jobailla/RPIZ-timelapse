#!/bin/bash
# file: extraTasks.sh
#
# This script will be launched in background after Witty Pi 2 get initialized.
# If you want to run your commands after boot, you can place them here.
#
sudo modprobe bcm2835-v4l2
cam=$(vcgencmd get_camera | cut -d '=' -f3)
if [ $cam != 0 ]; then
	sudo python3 /home/pi/RPIZ-timelapse/timelapse.py >> /home/pi/logs/timelapse.log 2>&1
#        gpio -g mode 4 out
else
        echo 'Camera not found'
fi

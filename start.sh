#!/bin/bash
# file: extraTasks.sh
#
# This script will be launched in background after Witty Pi 2 get initialized.
# If you want to run your commands after boot, you can place them here.
#
sudo modprobe bcm2835-v4l2
cam=$(vcgencmd get_camera | cut -d '=' -f3)

if [ $cam != 0 ]; then
	sudo python3 /home/pi/RPIZ-timelapse/timelapse.py >> /boot/timelapse/logs/timelapse.log 2>&1
	sudo cp /home/pi/wittyPi/schedule.log /boot/timelapse/logs/
	sudo cp /home/pi/wittyPi/wittyPi.log /boot/timelapse/logs/
#	sudo rclone copy /boot/timelpase/logs/timelapse.log onedrive:/Timelapse/Pictures/logs
#	sudo rclone copy /boot/timelapse/logs/schedule.log onedrive:/Timelapse/Pictures/logs
#	sudo rclone copy /boot/timelapse/logs/wittyPi.log onedrive:/Timelapse/Pictures/logs
#	gpio -g mode 4 out
else
	echo 'Camera not found'
fi

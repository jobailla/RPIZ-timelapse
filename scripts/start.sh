echo "\e[93m====================================================="
echo "\e[33m \e[4mDate/Time:\e[24m"
date
echo "\n\e[92mCamera activation\n"
sudo modprobe bcm2835-v4l2
echo "\e[34m \e[4mTake Picture:\e[24m"
sudo python3 /home/pi/RPIZ-timelapse/timelapse.py
echo "\n\e[35m \e[4mWittyPi schudule script:\e[24m\n"
sudo sh /home/pi/wittyPi/runScript.sh
echo "\n\e[92mSystem Shutdown..."
date
gpio -g mode 4 out
echo "\e[93m====================================================="

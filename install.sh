#! /bin/bash
echo -e "\e[33mSystem Update... \e[0m"
sudo apt-get update -y
echo -e "\e[33mInstalling Dependencies... \e[0m"
sudo apt-get install -y git vim python-picamera python-yaml python3-pip
sudo apt-get install -y proftpd
sudo apt-get install -y imagemagick
sudo apt-get install -y rclone
pip3 install picamera Werkzeug PyYAML 
mkdir /home/pi/Pictures
# Witty Pi
sudo su
echo "dtoverlay=w1-gpio,gpiopin=18" >> /boot/config.txt
exit
cd /home/pi
wget https://project-downloads.drogon.net/wiringpi-latest.deb
sudo dpkg -i wiringpi-latest.deb
wget http://www.uugear.com/repo/WittyPi2/installWittyPi.sh
sudo sh installWittyPi.sh
rm wiringpi-latest.deb
mv installWittyPi.sh wittyPi
echo "alias timelapse=\"python3 /home/pi/RPIZ-timelapse/timelapse.py\"" >> .bashrc
echo "alias witty=\"sudo /home/pi/wittyPi/wittyPi.sh\"" >> .bashrc
echo "alias test=\"python3 /home/pi/RPIZ-timelapse/test_camera.py\"" >> .bashrc
# activate camera
echo -e "\e[33mActivating Camera... (raspi-config)\e[0m"
raspi-config nonint do_camera 0
# disactivate HDMI
echo -e "\e[33mDisactivating HDMI... (.zshrc, /usr/bin/tvservice -p to reactivate)\e[0m"
/usr/bin/tvservice -o
if ! (grep -R "/usr/bin/tvservice -o" /home/pi/.zshrc 2>/dev/null)
then
    echo -e "\n/usr/bin/tvservice -o" >> /home/pi/.zshrc
fi
# set crontab
echo -e "\e[33mAdd crontab... \e[0m"
mkdir /home/pi/logs
( (crontab -l -u pi 2>/dev/null || echo "") ; echo "@reboot sudo sh /home/pi/RPIZ-timelapse/scripts/start.sh > /home/pi/logs/log.txt 2>&1") | sort - | uniq - | crontab - -u pi
# ask for reboot
read -p "Reboot Now (needed to restart wifi settings) ? (y/n) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
    echo -e "\n"
then
    reboot
fi

#! /bin/bash
echo -e "\e[33mSystem Update... \e[0m"
sudo apt-get update -y
echo -e "\e[33mInstalling Dependencies... \e[0m"
sudo apt-get install -y git vim python-picamera python-yaml python3-pip
read -p "Do you want install optionials dependencies ? (proftpd, imagemagick, rclone) ? (y/n) " yn
while true; do
	case $yn in
		[Yy]* ) echo -e "\e[33mInstalling Optionnals Dependencies... \e[0m" && sudo apt-get install -y proftpd imagemagick rclone; break;;
		[Nn]* ) exit;;
        	* ) echo "Please answer yes or no.";;
    	esac
done
echo -e "\e[33mInstalling Python Dependencies... \e[0m"
pip3 install picamera Werkzeug PyYAML 
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
if [ ! -d "/home/pi/Pictures" ]
	echo -e "\e[33mCreate Pictures directory...\e[0m"
then
	mkdir /home/pi/Pictures
fi
# set crontab
echo -e "\e[33mAdd crontab... \e[0m"
mkdir /home/pi/logs
( (crontab -l -u pi 2>/dev/null || echo "") ; echo "@reboot sudo sh /home/pi/RPIZ-timelapse/scripts/start.sh > /home/pi/logs/log.txt 2>&1") | sort - | uniq - | crontab - -u pi
# Witty Pi
if [ ! -d "/home/pi/wittyPi" ]
then
	echo -e "\e[33mWitty Pi setup...\e[0m"
	sudo echo "dtoverlay=w1-gpio,gpiopin=18" >> /boot/config.txt
	cd /home/pi
	wget https://project-downloads.drogon.net/wiringpi-latest.deb
	sudo dpkg -i wiringpi-latest.deb
	wget http://www.uugear.com/repo/WittyPi2/installWittyPi.sh
	sudo sh installWittyPi.sh
	rm wiringpi-latest.deb
	mv installWittyPi.sh wittyPi
	echo -e "\e[33mSet alias...\e[0m"
	echo "alias timelapse=\"sudo python3 /home/pi/RPIZ-timelapse/timelapse.py\"" >> .bashrc
	echo "alias witty=\"sudo /home/pi/wittyPi/wittyPi.sh\"" >> .bashrc
	echo "alias test=\"sudo python3 /home/pi/RPIZ-timelapse/test_camera.py\"" >> .bashrc
fi
# Timezone
echo "current timezone:"
sudo timedatectl | grep "Time zone:"
read -p "Do you want to change the timezone ? (raspi-config) ? (y/n) " yn
while true; do
	case $yn in
		[Yy]* ) sudo raspi-config; break;;
		[Nn]* ) exit;;
        	* ) echo "Please answer yes or no.";;
    	esac
done
# ask for reboot

read -p "Reboot Now (needed to restart wifi settings) ? (y/n) " yn
while true; do
	case $yn in
		[Yy]* ) sudo raspi-config; break;;
		[Nn]* ) exit;;
        	* ) echo "Please answer yes or no.";;
    	esac
done

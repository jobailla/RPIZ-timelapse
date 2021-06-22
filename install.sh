#! /bin/bash
echo -e "\e[33mSystem Update... \e[0m"
sudo apt-get update -y
echo -e "\e[33mInstalling Dependencies... \e[0m"
sudo apt-get install -y git vim dialog python-picamera python-yaml python3-pip
read -p "Do you want install optionials dependencies ? (proftpd, imagemagick, rclone) ? (y/n) " yn
case $yn in
	[Yy]* ) cmd=(dialog --separate-output --checklist "Select options:" 22 76 16)
		options=(1 "proftpd (ftp server)" off
		2 "imagemagick" off
		3 "rclone (cloud)" off)
		choices=$("${cmd[@]}" "${options[@]}" 2>&1 >/dev/tty)
		for choice in $choices
		do
			clear
			case $choice in
				1) sudo apt-get install -y proftpd;;
				2) sudo apt-get install -y imagemagick;;
				3) sudo apt-get install -y rclone;;
			esac
		done;;
	[Nn]* ) echo "";;
	* ) echo "Please answer yes or no.";;	
esac
echo -e "\e[33mInstalling Python Dependencies... \e[0m"
pip3 install pip3 install -r requirements.txt 
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
dialog --title "Do you want install Witty Pi mini ?" \
--backtitle "Install Witty Pi" \
--yesno "\nWitty Pi is small extension board that can add realtime clock and power management
to your Raspberry Pi. After installing Witty Pi on your Raspberry Pi, you get some
amazing new features:\n\n
- Gracefully turn on/off Raspberry Pi with single tap on the switch.\n
- Fully cuts power for Raspberry Pi and all its USB peripherals after shutdown.\n
- Raspberry Pi knows the correct time, even without accessing the Internet.\n
- You can schedule the startup/shutdown of your Raspberry Pi.\n
- You can even write a script to define complex ON/OFF sequence.\n
- When the OS loses response, you can long hold the switch to force power cut.\n\n
Witty Pi supports all Raspberry Pi models that has the 40-pin GPIO header, including
A+, B+, 2B, Zero and 3B.\n\n
This script will automatically do
these tasks in sequence:\n\n
- Enable I2C on your Raspberry Pi\n
- Install i2c-tools, if it is not installed yet\n
- Configure Bluetooth to use mini-UART (Raspberry Pi 3 only)\n
- Install wiringPi, if it is not installed yet\n
- Install Witty Pi programs, if they are not installed yet\n
- Remove fake-hwclock and disable ntpd daemon\n
- Install Qt 5, if it is not installed yet (it is optional, and is for Jessie only)\n
" 26 120
response=$?
case $response in
   1) clear && echo "Witty Pi mini will not install";;
   255) clear && echo "[ESC] key pressed.";;
   0)   clear
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
	else
		echo -e "\e[33mwittyPi folder already exists\e[0m"
	fi;;
esac
# Timezone
echo "current timezone:"
sudo timedatectl | grep "Time zone:"
read -p "Do you want to change the timezone ? (raspi-config) ? (y/n) " yn
while true; do
	case $yn in
		[Yy]* ) sudo raspi-config; break;;
		[Nn]* ) break;;
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

from picamera import PiCamera
import errno
import os
import sys
import threading
from datetime import datetime, timedelta
from time import sleep
import yaml
import subprocess

config = yaml.safe_load(open(os.path.join(sys.path[0], "config.yml")))
image_number = 0
image_list = []

dir_path = (str(config['dir_path']))
cloud_dir = (str(config['cloud_dir']))
cloud_name = (str(config['cloud_name']))
wittyPath = "/home/pi/wittyPi/"

def getDateTime():
    dateTime = subprocess.Popen('date', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    print('------------- ' + dateTime.strip('\n') + ' -------------')

def getUpTime():
    upTime = subprocess.Popen('uptime -s', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    timeUp = os.popen("awk '{print $1}' /proc/uptime").readline()
    seconds = str(round(float(timeUp)))
    print('RPI start:\t ', end = ' ')
    print(upTime, end = '')
    print('Uptime:\t\t  ' + str(timedelta(seconds = int(seconds))))

def getSystemInfo():
    cameraInfo = subprocess.Popen('vcgencmd get_camera', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    throttled = subprocess.Popen('vcgencmd get_throttled', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    temperature = subprocess.Popen('vcgencmd measure_temp', shell=True, stdout=subprocess.PIPE).stdout.read().decode().split('=')[1]
    
    throttledCode = throttled.split('=')[1].replace('\n', '')
    print(throttledCode + ': ', end = '')
    if throttledCode == '0x0':
        print('System stable', end = '')
    elif throttledCode == '0x1':
        print('Under-voltage detected', end = '')
    elif throttledCode == '0x2':
        print('Arm frequency capped', end = '')
    elif throttledCode == '0x4':
        print('Currently throttled', end = '')
    elif throttledCode == '0x8':
        print('Soft temperature limit active', end = '')
    elif throttledCode == '0x10000':
        print('Under-voltage has occurred', end = '')
    elif throttledCode == '0x20000':
        print('Arm frequency capping has occurred', end = '')
    elif throttledCode == '0x40000':
        print('Throttling has occurred', end = '')
    elif throttledCode == '0x80000':
        print('Soft temperature limit has occurred', end = '')
    else:
        print('Error', end = '')

    print(' / ', end = '')
    print('Cam: ' + cameraInfo.strip('\n'), end = '')
    print(' / ', end = '')
    print(temperature, end = '')

def set_schedule():
    scheduleTime = subprocess.Popen('date +%H:%M', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    
    if scheduleTime >= "21:00" and scheduleTime < "7:00":
        scheduleFile = "night.wpi"
    else:
        scheduleFile = "day.wpi"

    os.system("sudo rm -f " + wittyPath + "schedule.wpi")
    os.system("cp " + wittyPath + "schedules/" + scheduleFile + " " + wittyPath)
    os.system("mv " + wittyPath + scheduleFile + " " + wittyPath + "schedule.wpi")
    subprocess.call("sudo sh /home/pi/RPIZ-timelapse/run.sh", shell=True)

def set_camera_options(camera):
    # Set camera resolution.
    if config['resolution']:
        camera.resolution = (
            config['resolution']['width'],
            config['resolution']['height']
        )

    # Set ISO.
    if config['iso']:
        camera.iso = config['iso']

    # Set shutter speed.
    if config['shutter_speed']:
        camera.shutter_speed = config['shutter_speed']
        # Sleep to allow the shutter speed to take effect correctly.
        sleep(1)
        camera.exposure_mode = 'off'

    # Set white balance.
    if config['white_balance']:
        camera.awb_mode = 'off'
        camera.awb_gains = (
            config['white_balance']['red_gain'],
            config['white_balance']['blue_gain']
        )

    # Set camera rotation
    if config['rotation']:
        camera.rotation = config['rotation']

    return camera

def add_timestamp():
    for image in image_list:
        t = image.split("-")
        timestamp = t[2] + '\/' + t[1] + '\/' + t[0] + '\ ' + t[3] + '\:' + t[4] + '\:' + t[5].strip('.jpg')
        print ("add timestamp: " + image)
        os.system('convert ' + (dir_path + image + '  -pointsize 42 -fill yellow -annotate +100+100 ' + timestamp + ' ' + str(dir_path) + image))

# Upload picture(s) on cloud (Requires rclone)
def sync_cloud():
    print("uploading on " + str(cloud_name) + "...")
    os.system('sudo rclone copy ' + str(dir_path) + ' ' + str(cloud_name) + ':' + str(cloud_dir))

def capture_image():
    try:
        global image_number

        # Set a timer to take another picture at the proper interval after this
        # picture is taken.
        if (image_number < (config['total_images'] - 1)):
            thread = threading.Timer(config['interval'], capture_image).start()
        
        # Start up the camera.
        camera = PiCamera()
        set_camera_options(camera)
        
        # Capture a picture.
        image_name = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.jpg'
        camera.capture(str(dir_path) + image_name)
        camera.close()
        image_list.append(image_name)
        print(image_name.replace('.jpg', ''))
       
        if (image_number < (config['total_images'] - 1)):
            image_number += 1
        else:
            if config['add_timestamp']:
                add_timestamp()
            # sync cloud
            if config['upload_cloud']:
                sync_cloud()
            getDateTime()
            print('=========================================================\n')
    except (KeyboardInterrupt):
        print ("\nTime-lapse capture cancelled.\n")
        sys.exit()
    except (SystemExit):
        sys.exit()

# Create an animated gif (Requires ImageMagick)
def create_gif():
    print ('\nCreating animated gif.\n')
    os.system('convert -delay 10 -loop 0 ' + dir + '/image*.jpg ' + dir + '-timelapse.gif')

# Create a video (Requires avconv)
def create_video():
    print ('\nCreating video.\n')
    os.system('avconv -framerate 20 -i ' + dir + '/image%08d.jpg -vf format=yuv420p ' + dir + '/timelapse.mp4')

if __name__ == "__main__":
    # Print logs
    getDateTime()
    getSystemInfo()
    getUpTime()
    set_schedule()
    # Kick off the capture process
    print('Take Picture' + ('s' if config['total_images'] > 1 else '') + ':\t  ' , end = '')
    capture_image()
    # Optional actions
    if config['create_gif']:
        create_gif()
    if config['create_video']:
        create_video()
    # Shutdown
    if config['auto_shutdown']:
        print('System Shutdown', end = ' ')
        getDateTime()
        os.system('gpio -g mode 4 out')
    sys.exit()

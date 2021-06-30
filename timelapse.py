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

def getDateTime():
    dateTime = subprocess.Popen('date', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    print('\n\033[39m \033[4mTime:\t\t\033[24m ', end = ' ')
    print('\033[39m' + dateTime, end = '')

def getUpTime():
    upTime = subprocess.Popen('uptime -s', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    timeUp = os.popen("awk '{print $1}' /proc/uptime").readline()
    seconds = str(round(float(timeUp)))
    print('\n\033[35m \033[4mRPI start:\033[24m      ', end = ' ')
    print('\033[35m' + upTime, end = '')
    print(' uptime:\t  ' + str(timedelta(seconds = int(seconds))))

def getSystemInfo():
    cameraInfo = subprocess.Popen('vcgencmd get_camera', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    throttled = subprocess.Popen('vcgencmd get_throttled', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    temperature = subprocess.Popen('vcgencmd measure_temp', shell=True, stdout=subprocess.PIPE).stdout.read().decode()

    throttledCode = throttled.split('=')[1].replace('\n', '')
    print(' \033[36m' + throttledCode + ':', end = '')
    if throttledCode == '0x0':
        print(' \033[32mSystem stable')
    elif throttledCode == '0x1':
        print(' \033[31mUnder-voltage detected')
    elif throttledCode == '0x2':
        print(' \033[31mArm frequency capped')
    elif throttledCode == '0x4':
        print(' \033[31mCurrently throttled')
    elif throttledCode == '0x8':
        print(' \033[31mSoft temperature limit active')
    elif throttledCode == '0x10000':
        print(' \033[31mUnder-voltage has occurred')
    elif throttledCode == '0x20000':
        print(' \033[31mArm frequency capping has occurred')
    elif throttledCode == '0x40000':
        print(' \033[31mThrottling has occurred')
    elif throttledCode == '0x80000':
        print(' \033[31mSoft temperature limit has occurred')
    else:
        print(' \033[31mError')

    print('\033[36m Camera: ' + cameraInfo, end = '')
    print(' \033[36m' + temperature, end = '')

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
    print("\nuploading on " + str(cloud_name) + "...")
    os.system('rclone copy ' + str(dir_path) + ' ' + str(cloud_name) + ':' + str(cloud_dir))

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
        print('\t\t  ' + image_name.replace('.jpg', ''))
       
        if (image_number < (config['total_images'] - 1)):
            image_number += 1
        else:
            if config['add_timestamp']:
                add_timestamp()
            # sync cloud
            if config['upload_cloud']:
                sync_cloud()
            if config['auto_shutdown']:
                print('\n\033[92mSystem Shutdown...', end = '')
                getDateTime()
                os.system('gpio -g mode 4 out')
            print("\033[93m=====================================================")
            sys.exit()
    except (KeyboardInterrupt):
        print ("\nTime-lapse capture cancelled.\n")
        sys.exit()
    except (SystemExit):
        sys.exit()

# Print logs
getSystemInfo()
getUpTime()
getDateTime()

# Kick off the capture process
print('\033[34m Take Picture' + ('s' if config['total_images'] > 1 else '') + ':')
capture_image()


# Create an animated gif (Requires ImageMagick)
if config['create_gif']:
    print ('\nCreating animated gif.\n')
    os.system('convert -delay 10 -loop 0 ' + dir + '/image*.jpg ' + dir + '-timelapse.gif')

# Create a video (Requires avconv)
if config['create_video']:
    print ('\nCreating video.\n')
    os.system('avconv -framerate 20 -i ' + dir + '/image%08d.jpg -vf format=yuv420p ' + dir + '/timelapse.mp4')

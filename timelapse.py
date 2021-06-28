from picamera import PiCamera
import errno
import os
import sys
import threading
from datetime import datetime
from time import sleep
import yaml

config = yaml.safe_load(open(os.path.join(sys.path[0], "config.yml")))
image_number = 0
image_list = []

dir_path = (str(config['dir_path']))
cloud_dir = (str(config['cloud_dir']))
cloud_name = (str(config['cloud_name']))


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
        timestamp = t[2] + '\/' + t[1] + '\/' + t[0] + '\ ' + t[3] + '\:' + t[4] + '\:' + t[5]
        print ("add timestamp: " + image)
        os.system('convert ' + (dir_path + image + '  -pointsize 42 -fill yellow -annotate +100+100 ' + timestamp + ' ' + str(dir_path) + image))

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
        image_name = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f') + '.jpg'
        camera.capture(str(dir_path) + image_name)
        camera.close()
        image_list.append(image_name)
        print(image_name.replace('.jpg', ''))
       
        if (image_number < (config['total_images'] - 1)):
            image_number += 1
        else:
#            print ('\nTime-lapse capture complete!\n')
            if config['add_timestamp']:
                add_timestamp()
            # sync cloud
            if config['upload_cloud']:
                sync_cloud()
            sys.exit()
    except (KeyboardInterrupt):
#        print ("\nTime-lapse capture cancelled.\n")
        sys.exit()
    except (SystemExit):
#        print ("\nTime-lapse capture stopped.\n")
        sys.exit()


# Print where the files will be saved
#print("\nFiles will be saved in: " + str(dir_path) + "\n")
# Kick off the capture process.
date = os.system('date')
capture_image()

if config['create_gif']:
    print ('\nCreating animated gif.\n')
    os.system('convert -delay 10 -loop 0 ' + dir + '/image*.jpg ' + dir + '-timelapse.gif')

# Create a video (Requires avconv - which is basically ffmpeg).
if config['create_video']:
    print ('\nCreating video.\n')
    os.system('avconv -framerate 20 -i ' + dir + '/image%08d.jpg -vf format=yuv420p ' + dir + '/timelapse.mp4')

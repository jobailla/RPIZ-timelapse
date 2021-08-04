from picamera import PiCamera
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
timelapsePath = "/home/pi/RPIZ-timelapse/"


def getDateTime():
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    print('*************** ' + date + ' ' + time + ' ***************')


def getUpTime():
    upTime = subprocess.Popen('uptime -s', shell=True,
                              stdout=subprocess.PIPE).stdout.read().decode()
    timeUp = os.popen("awk '{print $1}' /proc/uptime").readline()
    seconds = str(round(float(timeUp)))
    print('RPI start:\t ', end=' ')
    print(upTime, end='')
    print('Uptime:\t\t  ' + str(timedelta(seconds=int(seconds))))


def getSystemInfo():
    GET_THROTTLED_CMD = 'vcgencmd get_throttled'
    GET_CAMERA_INFOS_CMD = 'vcgencmd get_camera'
    GET_TEMPERATURE_CMD = 'vcgencmd measure_temp'

    MESSAGES = {
        0: 'Under-voltage! ',
        1: 'ARM frequency capped! ',
        2: 'Currently throttled! ',
        3: 'Soft temperature limit active ',
        16: 'Under-voltage has occurred since last reboot. ',
        17: 'Throttling has occurred since last reboot. ',
        18: 'ARM frequency capped has occurred since last reboot. ',
        19: 'Soft temperature limit has occurred '
    }

    throttled_output = subprocess.Popen(
        GET_THROTTLED_CMD, shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    throttled_binary = bin(int(throttled_output.split('=')[1], 0))

    warnings = 0

    for position, message in MESSAGES.items():
        # Check for the binary digits to be "on" for each warning message
        if len(throttled_binary) > position and throttled_binary[0 - position - 1] == '1':
            warnings += 1

    if warnings == 0:
        print("System Stable", end='')
    else:
        print("Error: " + message, end='')

    cameraInfo = subprocess.Popen(
        GET_CAMERA_INFOS_CMD, shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    print(' / ', end='')
    print('Cam: ' + cameraInfo.strip('\n'), end='')
    print(' / ', end='')

    temperature = subprocess.Popen(
        GET_TEMPERATURE_CMD, shell=True, stdout=subprocess.PIPE).stdout.read().decode().split('=')[1]
    print(temperature, end='')


def calcul_time(date1, date2):
    date1 = date1.split(':')
    date2 = date2.split(':')
    date1 = [int(i) for i in date1]
    date2 = [int(i) for i in date2]
    date1 = timedelta(hours=date1[0], minutes=date1[1], seconds=date1[2])
    date2 = timedelta(hours=date2[0], minutes=date2[1], seconds=date2[2])
    diff = date2 - date1
    return diff


def str_to_delta(s):
    h, m, s = s.split(':')
    return timedelta(seconds=int(h) * 3600 + int(m) * 60 + int(s))


def set_schedule():
    time = datetime.now().time()
    date = datetime.now().date()

    time = timedelta(seconds=time.hour * 3600 + time.minute * 60 + time.second)

    reboot_interval = config['reboot_interval']

    night_start = config['night']['start']
    night_end = config['night']['end']

    date_start = config['date']['start']
    date_end = config['date']['end']

    start = str_to_delta(config['night']['start'])
    end = str_to_delta(config['night']['end'])

    on_min = config['on_min']
    print('Schedule:\t  ', end='')

    if time >= start or time <= end:
        print('NIGHT')
        date_start = date + timedelta(days=1)
        begin = str(date_start) + ' ' + str(time)
        end = str(date_end) + ' ' + str(night_end)
        time_off = (str_to_delta(night_end) - time).seconds - on_min
        time_on = on_min
    else:
        print('DAY')
        begin = str(date_start) + ' ' + str(night_end)
        end = str(date_end) + ' ' + str(night_start)
        time_off = reboot_interval - on_min
        time_on = on_min

    scheduleFile = open('schedule.wpi', 'w')
    scheduleFile.write('BEGIN' + '  ' + begin + '\n')
    scheduleFile.write('END' + '    ' + end + '\n')
    scheduleFile.write('ON' + '     ' + 'S' +
                       str(time_on) + ' ' + 'WAIT' + '\n')
    scheduleFile.write('OFF' + '    ' + 'S' + str(time_off) + '\n')
    scheduleFile.close()

    os.system("sudo rm -f " + wittyPath + "schedule.wpi")
    os.system("mv " + timelapsePath + "schedule.wpi" + " " + wittyPath)
    subprocess.call("sudo sh " + timelapsePath + "run.sh", shell=True)


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
        timestamp = t[2] + '\/' + t[1] + '\/' + t[0] + '\ ' + \
            t[3] + '\:' + t[4] + '\:' + t[5].strip('.jpg')
        print("add timestamp: " + image)
        os.system('convert ' + (dir_path + image + '  -pointsize 42 -fill yellow -annotate +100+100 ' +
                  timestamp + ' ' + str(dir_path) + image))

# Upload picture(s) on cloud (Requires rclone)


def sync_cloud():
    print("uploading on " + str(cloud_name) + "...")
    os.system('sudo rclone copy ' + str(dir_path) + ' ' +
              str(cloud_name) + ':' + str(cloud_dir))


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
            print('===================================================\n')
    except (KeyboardInterrupt):
        print("\nTime-lapse capture cancelled.\n")
        sys.exit()
    except (SystemExit):
        sys.exit()

# Create an animated gif (Requires ImageMagick)


def create_gif():
    print('\nCreating animated gif.\n')
    os.system('convert -delay 10 -loop 0 ' + dir +
              '/image*.jpg ' + dir + '-timelapse.gif')

# Create a video (Requires avconv)


def create_video():
    print('\nCreating video.\n')
    os.system('avconv -framerate 20 -i ' + dir +
              '/image%08d.jpg -vf format=yuv420p ' + dir + '/timelapse.mp4')


# Main function
if __name__ == "__main__":
    # Print logs
    getDateTime()
    getSystemInfo()
    getUpTime()
    set_schedule()
    # Kick off the capture process
    print('Take Picture' +
          ('s' if config['total_images'] > 1 else '') + ':\t', end='')
    capture_image()
    # Optional actions
    if config['create_gif']:
        create_gif()
    if config['create_video']:
        create_video()
    # Shutdown
    if config['auto_shutdown']:
        os.system('gpio -g mode 4 out')
    sys.exit()

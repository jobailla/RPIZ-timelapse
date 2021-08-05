from picamera import PiCamera
import os
import sys
import threading
from datetime import datetime, timedelta
from time import sleep
import yaml
import subprocess

# Config from yaml file
CONFIG = yaml.safe_load(open(os.path.join(sys.path[0], "config.yml")))
# Variables
IMAGE_NUMBER = 0
IMAGE_LIST = []
REBOOT_INTERVAL = (int(CONFIG['reboot_interval']))
TOTAL_IMAGES = (int(CONFIG['total_images']))
CAPTURE_INTERVAL = (int(CONFIG['interval']))
ON_MIN = CONFIG['on_min']
ANNOTATE_TIME_COLOR = 'yellow'
BOOL_CREATE_GIF = CONFIG['create_gif']
BOOL_CREATE_VIDEO = CONFIG['create_video']
BOOL_AUTO_SHUTDOWN = CONFIG['auto_shutdown']
BOOL_ADD_ANNOTATION = CONFIG['add_timestamp']
BOOL_UPLOAD_CLOUD = CONFIG['upload_cloud']
# images
PICTURE_NAME_DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'
PICTURE_EXTENSTION = '.jpg'
# Cloud
CLOUD_DIR = (str(CONFIG['cloud_dir']))
CLOUD_NAME = (str(CONFIG['cloud_name']))
# Date and time
DATE_START = (str(CONFIG['date']['start']))
DATE_END = (str(CONFIG['date']['end']))
NIGHT_START = (str(CONFIG['night']['start']))
NIGHT_END = (str(CONFIG['night']['end']))
# Paths
DIR_PATH = (str(CONFIG['dir_path']))
WITTY_PATH = "/home/pi/wittyPi/"
TIMELAPSE_PATH = "/home/pi/RPIZ-timelapse/"
# Files names
SCHEDULE_FILE = 'schedule.wpi'
WITTY_RUN_SCHEDULE_FILE = 'run.sh'
# Cammands
GET_THROTTLED_CMD = 'vcgencmd get_throttled'
GET_CAMERA_INFOS_CMD = 'vcgencmd get_camera'
GET_TEMPERATURE_CMD = 'vcgencmd measure_temp'
GET_UPTIME_CMD = 'uptime -s'
GET_UPTIME_SECONDS_CMD = "awk '{print $1}' /proc/uptime"
SHUTDOWN_CMD = 'gpio -g mode 4 out'
# Camera settings
CAMERA_RESOLUTION = CONFIG['resolution']
CAMERA_ROTATION = CONFIG['rotation']
CAMERA_WIDTH = CAMERA_RESOLUTION['width']
CAMERA_HEIGHT = CAMERA_RESOLUTION['height']
CAMERA_FRAMERATE = CONFIG['framerate']
CAMERA_ISO = CONFIG['iso']
CAMERA_BRIGHTNESS = CONFIG['brightness']
CAMERA_CONTRAST = CONFIG['contrast']
CAMERA_SHUTTERSPEED = CONFIG['shutterspeed']
CAMERA_WHITE_BALANCE = CONFIG['white_balance']
CAMERA_RED_GAIN = CAMERA_WHITE_BALANCE['red_gain']
CAMERA_BLUE_GAIN = CAMERA_WHITE_BALANCE['blue_gain']
# Logs messages
THROTTLED_MESSAGES = {
    0: 'Under-voltage! ',
    1: 'ARM frequency capped! ',
    2: 'Currently throttled! ',
    3: 'Soft temperature limit active ',
    16: 'Under-voltage has occurred since last reboot. ',
    17: 'Throttling has occurred since last reboot. ',
    18: 'ARM frequency capped has occurred since last reboot. ',
    19: 'Soft temperature limit has occurred '
}
ASCII_STARS = '***************'
ASCII_LINE = '==================================================='

# Get and print current time
def getDateTime():
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    print(ASCII_STARS + ' ' + date + ' ' + time + ' ' + ASCII_STARS)

# Get and print Rapsberry Pi uptime
def getUpTime():
    up_time = subprocess.Popen('GET_UPTIME_CMD', shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    up_time_seconds = os.popen(GET_UPTIME_SECONDS_CMD).readline()
    seconds = str(round(float(up_time_seconds)))
    print('RPI start:\t ', end=' ')
    print(up_time, end='')
    print('Uptime:\t\t  ' + str(timedelta(seconds=int(seconds))))

# Get and print Raspberry Pi system info
def getSystemInfo():
    throttled_output = subprocess.Popen(GET_THROTTLED_CMD, shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    throttled_binary = bin(int(throttled_output.split('=')[1], 0))
    warnings = 0

    for position, message in THROTTLED_MESSAGES.items():
        # Check for the binary digits to be "on" for each warning message
        if len(throttled_binary) > position and throttled_binary[0 - position - 1] == '1':
            warnings += 1
    if warnings == 0:
        print("System Stable", end='')
    else:
        print("Error: " + message, end='')

    cameraInfo = subprocess.Popen(GET_CAMERA_INFOS_CMD, shell=True, stdout=subprocess.PIPE).stdout.read().decode()
    print(' / ', end='')
    print('Cam: ' + cameraInfo.strip('\n'), end='')
    print(' / ', end='')

    temperature = subprocess.Popen(GET_TEMPERATURE_CMD, shell=True, stdout=subprocess.PIPE).stdout.read().decode().split('=')[1]
    print(temperature, end='')

# Calculate time between two timedelta
def calcul_time(date1, date2):
    date1 = date1.split(':')
    date2 = date2.split(':')
    date1 = [int(i) for i in date1]
    date2 = [int(i) for i in date2]
    date1 = timedelta(hours=date1[0], minutes=date1[1], seconds=date1[2])
    date2 = timedelta(hours=date2[0], minutes=date2[1], seconds=date2[2])
    diff = date2 - date1
    return diff

# Convert string to timedelta
def str_to_delta(s):
    h, m, s = s.split(':')
    return timedelta(seconds=int(h) * 3600 + int(m) * 60 + int(s))

# Create schedule file
def write_schedule(end, begin, time_off, time_on):
    scheduleFile = open(WITTY_PATH + SCHEDULE_FILE, 'w')
    scheduleFile.write('BEGIN' + '  ' + begin + '\n')
    scheduleFile.write('END' + '    ' + end + '\n')
    scheduleFile.write('ON' + '     ' + 'S' + str(time_on) + ' ' + 'WAIT' + '\n')
    scheduleFile.write('OFF' + '    ' + 'S' + str(time_off) + '\n')
    scheduleFile.close()

# Calcul day/night periode, wirte on schedule file and run witty runscript
def set_schedule():
    time = datetime.now().time()
    time = timedelta(seconds=time.hour * 3600 + time.minute * 60 + time.second)
    date = datetime.now().date()
    start = str_to_delta(NIGHT_START)
    end = str_to_delta(NIGHT_END)

    print('Schedule:\t  ', end='')

    if time >= start or time <= end:
        print('NIGHT')
        date_start = date + timedelta(days=1)
        begin = str(date_start) + ' ' + str(time)
        end = str(DATE_END) + ' ' + str(NIGHT_END)
        time_off = (str_to_delta(NIGHT_END) - time).seconds - ON_MIN
        time_on = ON_MIN
    else:
        print('DAY')
        begin = str(DATE_START) + ' ' + str(NIGHT_END)
        end = str(DATE_END) + ' ' + str(NIGHT_START)
        time_off = REBOOT_INTERVAL - ON_MIN
        time_on = ON_MIN

    os.system("sudo rm -f " + WITTY_PATH + SCHEDULE_FILE)
    write_schedule(end, begin, time_off, time_on)

    subprocess.call("sudo sh " + TIMELAPSE_PATH + WITTY_RUN_SCHEDULE_FILE, shell=True)

# Camera configuration
def set_camera_options(camera):
    # Set camera resolution.
    if CAMERA_RESOLUTION:
        camera.resolution = (CAMERA_WIDTH, CAMERA_HEIGHT)
    # Set ISO.
    if CAMERA_ISO:
        camera.iso = CAMERA_ISO
    # Set shutter speed.
    if CAMERA_SHUTTERSPEED:
        camera.shutter_speed = CAMERA_SHUTTERSPEED
        # Sleep to allow the shutter speed to take effect correctly.
        sleep(1)
        camera.exposure_mode = 'off'
    # Set white balance.
    if CAMERA_WHITE_BALANCE:
        camera.awb_mode = 'off'
        camera.awb_gains = (CAMERA_RED_GAIN, CAMERA_BLUE_GAIN)
    # Set camera rotation
    if CAMERA_ROTATION:
        camera.rotation = CAMERA_ROTATION
    return camera

# Annotate image with time of capture
def annotate_image():
    for image in IMAGE_LIST:
        t = image.split("-")
        timestamp = t[2] + '\/' + t[1] + '\/' + t[0] + '\ ' + \
            t[3] + '\:' + t[4] + '\:' + t[5].strip('.jpg')
        print("add timestamp: " + image)
        os.system('convert ' + (DIR_PATH + image + '  -pointsize 42 -fill ' + ANNOTATE_TIME_COLOR + ' -annotate +100+100 ' +
                  timestamp + ' ' + str(DIR_PATH) + image))

# Upload picture(s) on cloud (Requires rclone)
def sync_cloud():
    print("uploading on " + str(CLOUD_NAME) + "...")
    os.system('sudo rclone copy ' + str(DIR_PATH) + ' ' +
              str(CLOUD_NAME) + ':' + str(CLOUD_DIR))

def capture_image():
    try:
        global IMAGE_NUMBER
        # Set a timer to take another picture at the proper interval after this
        # picture is taken.
        if (IMAGE_NUMBER < TOTAL_IMAGES - 1):
            thread = threading.Timer(CAPTURE_INTERVAL, capture_image).start()

        # Start up the camera.
        camera = PiCamera()
        set_camera_options(camera)
        # Capture a picture.
        image_name = datetime.now().strftime(PICTURE_NAME_DATETIME_FORMAT) + PICTURE_EXTENSTION
        camera.capture(str(DIR_PATH) + image_name)
        camera.close()
        IMAGE_LIST.append(image_name)
        print(image_name.replace(PICTURE_EXTENSTION, ''))

        if (IMAGE_NUMBER < TOTAL_IMAGES - 1):
            IMAGE_NUMBER += 1
        else:
            if BOOL_ADD_ANNOTATION:
                annotate_image()
            # sync cloud
            if BOOL_UPLOAD_CLOUD:
                sync_cloud()
            getDateTime()
            print(ASCII_LINE + '\n')
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
    os.system('avconv -framerate 20 -i ' + dir + '/image%08d.jpg -vf format=yuv420p ' + dir + '/timelapse.mp4')

# Main function
if __name__ == "__main__":
    # Print logs
    getDateTime()
    getSystemInfo()
    getUpTime()
    set_schedule()
    # Kick off the capture process
    print('Take Picture' + ('s' if TOTAL_IMAGES > 1 else '') + ':\t', end='')
    capture_image()
    # Optional actions
    if BOOL_CREATE_GIF:
        create_gif()
    if BOOL_CREATE_VIDEO:
        create_video()
    # Shutdown
    if BOOL_AUTO_SHUTDOWN:
        os.system(SHUTDOWN_CMD)
    sys.exit()

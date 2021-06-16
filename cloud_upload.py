import os
import sys
import yaml

config = yaml.safe_load(open(os.path.join(sys.path[0], "config.yml")))

dir_path = (str(config['dir_path']))
cloud_dir = (str(config['cloud_dir']))
cloud_name = (str(config['cloud_name']))

print("\nuploading on " + str(cloud_name) + "...")
os.system('rclone copy ' + str(dir_path) + ' ' + str(cloud_name) + ':' + str(cloud_dir))

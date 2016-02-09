import os
import sys
import yaml
import boto
import time
from hashlib import md5
from calendar import timegm
from IPython import embed

def error(msg):
    print "ERROR:", msg
    
def info(msg):
    # TODO use logging module
    pass # print" INFO:", msg
    
def fatal_error(msg):
    error(msg)
    sys.exit(1)
    
def md5sum(filename):
    with open(filename, "r") as f:
        return md5(f.read()).hexdigest()
        
def modified_time(key):
    return timegm(time.strptime(key.last_modified, "%a, %d %b %Y %H:%M:%S %Z"))
    
def ensure_folder(folder):
    if not os.path.exists(folder):  
        os.makedirs(folder)  

class OpenS3Box:

    def __init__(self, config_file):
        with open(config_file, "r") as f:
            self.config = yaml.load(f)
        
        try:
            self.aws_key_id = self.config["aws.key_id"]
            self.aws_key = self.config["aws.key"]
            self.aws_host = self.config["aws.host"]
            self.remote_bucket = self.config["remote.bucket"]
            self.local_folder = self.config["local.folder"]
        except KeyError, e:
            fatal_error("Missing configuration {}".format(e.args[0]))
        
        if not os.path.isdir(self.local_folder):
            print error("{} does not exist".format(self.local_folder))
            
        self.conn = boto.connect_s3(self.aws_key_id, self.aws_key,\
                                    is_secure=True, host=self.aws_host)
        self.bucket = self.conn.get_bucket(self.remote_bucket)
        
    def local_to_remote_path(self, *args):
        return os.path.join(*args).replace(self.local_folder, "").replace("\\", "/")[1:]
        
    def remote_to_local_path(self, key):
        return os.path.join(self.local_folder, key.name.replace("/", os.sep))
        
    def sync(self):
        # TODO add caching: md5sum/data modified/...
        # Download new or modified files
        info("Checking S3 files")
        for key in self.bucket.list():
            local_path = self.remote_to_local_path(key)
            ensure_folder(os.path.dirname(local_path))

            if not os.path.isfile(local_path):
                info("Downloading new file {}".format(local_path))
                key.get_contents_to_filename(local_path)
            elif md5sum(local_path) != key.etag[1:-1]:
                if os.path.getmtime(local_path) < modified_time(key):
                    key.get_contents_to_filename(local_path)
            else:
                info("File up to date {}".format(key.name))
        
        # Upload new or modified files
        info("Checking local files")
        for root, dirs, files in os.walk(self.local_folder):
            for filename in files:
                local_path = os.path.join(root, filename)
                key_path = self.local_to_remote_path(root, filename)
                key = self.bucket.get_key(key_path)
                if key is None:
                    info("Uploading new file {}".format(key_path))
                    key = boto.s3.key.Key(self.bucket, key_path)
                    key.set_contents_from_filename(local_path)
                elif md5sum(local_path) != key.etag[1:-1]:
                    # This logic is flawed and can cause data loss, but should work in most simple scenarios
                    if os.path.getmtime(local_path) > modified_time(key):
                        info("Uploading modified file {}".format(key_path))
                        key.set_contents_from_filename(local_path)
                else:
                    info("File up to date {}".format(key_path))

if __name__ == "__main__":
    opens3box = OpenS3Box("opens3box.conf")
    
    opens3box.sync()
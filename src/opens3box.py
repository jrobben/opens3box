import os
import sys
import yaml
import boto
import time
import json
from hashlib import md5
from calendar import timegm
from IPython import embed
from tray import SysTrayIcon

def error(msg):
    # TODO linux support
    print "ERROR:", msg
    import win32api
    win32api.MessageBox(0, msg, "Error")

def info(msg):
    # TODO use logging module
    print" INFO:", msg
    
def fatal_error(msg):
    error(msg)
    sys.exit(1)
    
def md5sum(filename):
    with open(filename, "r") as f:
        return md5(f.read()).hexdigest()
        
def modified_time(key):
    try:
        return timegm(time.strptime(key.last_modified, "%a, %d %b %Y %H:%M:%S %Z"))
    except ValueError:
        return timegm(time.strptime(key.last_modified[:19], "%Y-%m-%dT%H:%M:%S"))
    
def ensure_folder(folder):
    if not os.path.exists(folder):  
        os.makedirs(folder)

def get_user_folder():
    # TODO linux support
    return os.path.join(os.getenv('USERPROFILE'), ".opens3box")

class OpenS3Box:

    def __init__(self):
        self.user_folder = get_user_folder()
        ensure_folder(self.user_folder)

        self.load_config()
        self.load_cache()
        
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

    def load_config(self):
        config_file = os.path.join(self.user_folder, "opens3box.conf")
        try:
            with open(config_file, "r") as f:
                self.config = yaml.load(f)
        except IOError:
            fatal_error(config_file + " does not exist.")

    def get_cache_file(self):
        return os.path.join(self.user_folder, ".cache")

    def load_cache(self):
        try:
            with open(self.get_cache_file(), "r") as f:
                self.cache = json.load(f)
        except IOError:
            self.cache = {"mtime" : {}, "version": {}, "md5": {}}

    def write_cache(self):
        info("Writing cache")
        with open(self.get_cache_file(), "w") as f:
            json.dump(self.cache, f)

    def local_to_remote_path(self, *args):
        return os.path.join(*args).replace(self.local_folder, "").replace("\\", "/")[1:]
        
    def remote_to_local_path(self, key):
        return os.path.join(self.local_folder, key.name.replace("/", os.sep))
        
    def download(self, key, local_path):
       try:
            key.get_contents_to_filename(local_path)
            self.cache_metadata(local_path, self.get_remote_version(key))
       except Exception, e:
            embed()
            error("Failed to update {}, {}".format(local_path, str(e)))

    def upload(self, key, local_path, version):
        key.set_contents_from_filename(local_path)
        key = self.set_metadata(key, version, local_path)
        self.cache_metadata(local_path, version)
        return key

    def get_remote_version(self, key):
        try:
            if key is None:
                return 0

            version = key.get_metadata("version")
            if version is None:
                return 0

            return int(version)
        except KeyError:
            return 0

    def get_remote_modified_time(self, key):
        try:
            if key is None:
                return 0

            mtime = key.get_metadata("mtime")
            if mtime is None:
                return 0

            return int(mtime)
        except KeyError:
            return 0

    def get_local_modified_time(self, local_path):
        return int(os.path.getmtime(local_path))

    def _get_cache_key(self, local_path):
        return local_path.replace(self.local_folder, "")

    def get_local_version(self, local_path):
        try:
            return self.cache["version"][self._get_cache_key(local_path)]
        except KeyError:
            return 0

    def get_cached_modified_time(self, local_path):
        try:
            return self.cache["mtime"][self._get_cache_key(local_path)]
        except KeyError:
            return 0

    def get_cached_md5sum(self, local_path):
        try:
            return self.cache["md5"][self._get_cache_key(local_path)]
        except KeyError:
            return 0

    def set_metadata(self, key, version, local_path):
        return key.copy(key.bucket.name, key.name, {"version": version, "mtime": self.get_local_modified_time(local_path)}, preserve_acl=True)

    def cache_metadata(self, local_path, version):
        self.cache["mtime"][self._get_cache_key(local_path)] = self.get_local_modified_time(local_path)
        self.cache["version"][self._get_cache_key(local_path)] = version
        self.cache["md5"][self._get_cache_key(local_path)] = md5sum(local_path)

        
    def sync(self):
        # TODO add caching: md5sum/data modified/...
        # Download new or modified files
        info("Checking S3 files")
        for key in self.bucket.list():
            local_path = self.remote_to_local_path(key)
            ensure_folder(os.path.dirname(local_path))

            if not os.path.isfile(local_path):
                info("Downloading new file {}".format(local_path))
                self.download(key, local_path)
        self.write_cache()
        
        # Upload new or modified files
        info("Checking local files")
        for root, dirs, files in os.walk(self.local_folder):
            for filename in files:
                local_path = os.path.join(root, filename)
                key_path = self.local_to_remote_path(root, filename)
                key = self.bucket.get_key(key_path)

                local_version = self.get_local_version(local_path)
                remote_version = self.get_remote_version(key)
                remote_mtime = self.get_remote_modified_time(key)

                remote_file_changed = remote_version > local_version
                local_file_changed = self.get_local_modified_time(local_path) > self.get_cached_modified_time(local_path)\
                                        and md5sum(local_path) != self.get_cached_md5sum(local_path)

                if key is None:
                    info("Uploading new file {}".format(key_path))
                    key = boto.s3.key.Key(self.bucket, key_path)
                    self.upload(key, local_path, 1)
                elif remote_file_changed and local_file_changed:
                    error("{}\nBoth local and remote files have changed.\nRemove local or remote file.".format(local_path))
                elif local_file_changed:
                    info("File {} has changed, uploading..".format(local_path))
                    self.upload(key, local_path, local_version+1)
                elif remote_file_changed:
                    info("A new version of {} is available, downloading..".format(local_path))
                    self.download(key, local_path)
                else:
                    info("File up to date {}".format(key_path))
        self.write_cache()

if __name__ == '__main__':
    icon = "../resources/icon.ico"
    hover_text = "OpenS3Box"
    opens3box = OpenS3Box()
    def sync(sysTrayIcon):
        opens3box.sync()
    def close(sysTrayIcon):
        pass
    menu_options = [('Sync', icon, sync)]
    
    SysTrayIcon(icon, hover_text, menu_options, on_quit=close, default_menu_index=1)
    opens3box.write_cache()
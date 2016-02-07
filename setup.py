import os
from distutils.core import setup
import py2exe

# Fix for: pywintypes27.dll not found
import site
for site_path in site.getsitepackages():
    pywin32_path = os.path.join(site_path, "pywin32_system32")
    if os.path.isdir(pywin32_path):
        os.environ["PATH"] = os.environ["PATH"] + ";" + pywin32_path

setup(console=['opens3box.py'])
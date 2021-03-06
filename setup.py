import os
import sys
from distutils.core import setup
import py2exe

sys.path.append("src")

# Fix for: pywintypes27.dll not found
import site
for site_path in site.getsitepackages():
    pywin32_path = os.path.join(site_path, "pywin32_system32")
    if os.path.isdir(pywin32_path):
        os.environ["PATH"] = os.environ["PATH"] + ";" + pywin32_path

setup(windows=['src/opens3box.py'],
options={
'py2exe': {'includes': ['tray']},
}   
)

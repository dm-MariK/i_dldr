import os

# If the script was started with "system" version of python, we want to replace 
# the Python interpreter with a custom one from the preconfigured Conda environment.
# Path to the python binary in the Conda environment:
TARGET_PYTHON = "/home/<USER>/.local/bin/miniconda3/envs/<ICLOUD_ENV_NAME>/bin/python"
# To obtain correct value, run the following while being in your preconfigured Conda environment:
#`(icloud_env) user@localhost:~$ which python`
# should return something like this:
#/home/user/.local/bin/miniconda3/envs/icloud_env/bin/python
# In the example above it is assumed that your local account is 'user' 
# and Conda environment is called 'icloud_env'

DEBUG_MODE = True
#DEBUG_MODE = False

# 
SOCKET_TIMEOUT = None # the default behavior, set value in seconds, like:
#SOCKET_TIMEOUT = 300 # 5 minutes

# Your e-mail that is used as Apple ID:
APPLE_ID = "your_email@example.com"

# Album name on the iCloud Photo:
ALBUM_NAME = "Screenshots"
# Run the `dldr.py -o` (or `dldr.py --auth-only) to obtain the list of all available albums
# with their correct names.

# Local directory to download to:
DOWNLOAD_DIR = os.path.expanduser("~/Downloads/iCloud/Screenshots")

import PyInstaller.__main__
import os

# Ensure the icon exists, or create a dummy one if you don't have it yet to prevent build errors
if not os.path.exists("buttstrapper.ico"):
    print("WARNING: buttstrapper.ico not found. Using default icon.")
    icon_arg = []
else:
    icon_arg = ['--icon=buttstrapper.ico']

print("Building Buttstrapper Release 1...")

PyInstaller.__main__.run([
    'fflag_manager.py',
    '--name=ButtstrapperPro',
    '--onefile',
    '--noconsole',
    '--clean',
    '--add-data=fflag_manager.py;.'  # Adds itself if needed for reference, usually not required for onefile logic but good for metadata
] + icon_arg)

print("Build Complete! Check the /dist folder.")
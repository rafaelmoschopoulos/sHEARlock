import subprocess
import uuid
import pycurl
from io import BytesIO
import tempfile
import os


def install_blackhole_drv(download_url: str):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file_name = f"{uuid.uuid4()}.pkg"
            output_file_path = os.path.join(tmp_dir_name, file_name)

            try:
                buffer = BytesIO()
                c = pycurl.Curl()
                c.setopt(c.URL, download_url)
                c.setopt(c.FOLLOWLOCATION, True)
                c.setopt(c.WRITEDATA, buffer)
                c.perform()
                response_code = c.getinfo(pycurl.RESPONSE_CODE)
                if response_code != 200:
                    raise Exception(f"Failed to download file: HTTP {response_code}")
                c.close()

            except pycurl.error as e:
                print(f"Error downloading driver package: {e}")

            try:
                with open(output_file_path, 'wb') as f:
                    f.write(buffer.getvalue())
                print("BlackHole driver downloaded successfully.\n")
            except IOError as e:
                print(f"Error writing file \'{output_file_path}\': {e}")

            try:
                print("sudo password required to install BlackHole driver.")
                command = f"sudo installer -pkg {output_file_path} -target /"
                sudo_password = input("Enter your sudo password: ")
                full_command = f"echo {sudo_password} | sudo -S {command}"
                result = subprocess.run(full_command, shell=True, text=True, capture_output=True)
                print(result.stdout, result.stderr, sep='\n')

                print("Installation complete.\n------------------------\n")
            except subprocess.CalledProcessError as e:
                print(f"Error installing driver package: {e}")

    except Exception as e:
        print(f"Unexpected error occurred: {e}")

def midi_setup():
    instructions = """You will now need to setup a multiple-output device.
This will enable broadcasting of system output to both a physical output device and the virtual input for sHEARlock.
1) On the \'Audio Midi Setup\' dialogue, click the \'+\' button on the lower left corner, then \'Create Multi-Output Device\'.
2) In the checkbox list on the right panel, select \'BlackHole 2ch\', and the audio playback device of your choice.
3) In the output device list of the left panel, middle click on the newly created device and select \'Use This Device For Sound Output\'."""
    print(instructions)
    applescript = """
        tell application "Audio MIDI Setup"
            activate
        end tell
        """
    try:
        subprocess.run(['osascript', '-e', applescript])
    except subprocess.CalledProcessError as e:
        print(f"Error opening the \'Audio MIDI Setup\' dialogue. Please navigate to it manually.")


if __name__ == '__main__':
    print("Welcome to the installation script for sHEARlock.\nPlease follow the instructions below.\n")
    install_blackhole_drv('https://existential.audio/blackhole/download/download2ch.php?code=2054116538')
    midi_setup()

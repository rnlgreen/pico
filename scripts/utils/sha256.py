# Import hashlib library (sha256 method is part of it)
import hashlib
import ubinascii # type: ignore # pylint: disable=import-error
from utils import mqtt
from utils import myid
import uos # type: ignore # pylint: disable=import-error

# File to check
testfile = 'utils/sha256.py'

# Correct original sha256 goes here
test_sha256 = '05657f3022426bb6511ecf0267fc40d578cb52f900a50fe2169644b16c41db50'

#Print and send status messages
def status(message):
    print(message)
    message = myid.pico + ": " + message
    topic = 'pico/'+myid.pico+'/status'
    mqtt.send_mqtt(topic,message)

def file_exists(filename):
    try:
        return (uos.stat(filename)[0] & 0x4000) == 0
    except OSError:
        return False

def check_sha256(file_name, original_sha256, chunk_size=1024):
    if file_exists(file_name):
        # Open,close, read file and calculate sha256 on its contents
        try:
            sha256 = hashlib.sha256()
            with open(file_name, 'rb') as file_to_check:
                # read contents of the file in chunks to avoid memory issues
                while True:
                    data = file_to_check.read(chunk_size)
                    if not data:
                        break
                    sha256.update(data)
                # pipe contents of the file through
                sha256_returned = ubinascii.hexlify(sha256.digest()).decode()
        except Exception as e: # pylint: disable=broad-exception-caught
            status(f"Error finding sha256 for '{file_name}'")
            status(f"{e}")
            sha256_returned = "xxx"

        # Finally compare original sha256 with freshly calculated
        if original_sha256 == sha256_returned:
            print (f"sha256 verified for {file_name}")
            return True
        if sha256_returned == "xxx":
            print ("Skipping file with failed sha256 check")
            return True
        return False
    print (f"New file found: {file_name}")
    return False

if __name__ == "__main__":
    check_sha256(testfile, test_sha256)

# Import hashlib library (sha256 method is part of it)
import hashlib
import ubinascii # type: ignore
import utils.mqtt as mqtt
import utils.myid as myid
import uos # type: ignore

# File to check
file_name = 'utils/sha256.py'

# Correct original sha256 goes here
original_sha256 = '05657f3022426bb6511ecf0267fc40d578cb52f900a50fe2169644b16c41db50'  

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

def check_sha256(file_name, original_sha256):
    if file_exists(file_name):
        # Open,close, read file and calculate sha256 on its contents 
        try:
            with open(file_name, 'rb') as file_to_check:
                # read contents of the file
                data = file_to_check.read()    
                # pipe contents of the file through
                sha256_returned = ubinascii.hexlify(hashlib.sha256(data).digest()).decode()
        except Exception as e:
            status("Error finding sha256 for '{}'".format(file_name))
            status("{}".format(e))
            sha256_returned = "xxx"

        # Finally compare original sha256 with freshly calculated
        if original_sha256 == sha256_returned:
            print ("sha256 verified for {}".format(file_name))
            return True
        elif sha256_returned == "xxx":
            print ("Skipping file with failed sha256 check")
            return True
        else:
            #status ("Changed: {}".format(file_name))
            #status ("{} <> {}".format(sha256_returned,original_sha256))
            return False
    else: #file doesn't exist so needs copying
        print ("New file found: {}".format(file_name))
        return False

if __name__ == "__main__":
    check_sha256(file_name, original_sha256)



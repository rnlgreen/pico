A set of scripts I use with my Rapberry PI Pico W boards.

My aim was to create a command and control architecture for these boards that would enable me to monitor and manage them remotely once I've manually put the code library on once using rshell / rsync.

I ackowledge up front that I am not the greatest Python coder; you won't find many classes in my code, and I've magpied a lot of other people's code into this collection.

The scripts included in this repo are:

main.py The main routine that is run by the pico when it is powered up. All picos run the same main.py, and it performs the following functions:
* calls the get_id() function from my myid module to determine which of my picos this is
* calls the wlan_connect() function from my wifi module to connect to wifi
* calls the set_time() function from my ntp module to sync the real time clock
* calls the mqtt_connect() function from my mqtt module to connect to my local MQTT server
* sends status updates via MQTT (which are picked up by a Node-RED dashboard, which in turn sends alerts on to Slack channels)
* subscribes to 'control' and 'poll' MQTT topics so that the Node-RED dashboard can send heartbeats and control commands
* finally imports a specific module based on the name of this pico and calls main() in that module

As well as responding to polling messages received over MQTT, main.py also responds to the following commands received on the 'pico/pico[n]/control' topic:
* 'blink' - causes the pico LED to blink, handy to make sure you know which is which!
* 'reload' - causes the pico to FTP the latest set of python scripts from an FTP repository, using SHA256 checksums to work out which ones need updating
* 'restart' - causes the pico to execute the machine.restart() method to reboot the pico
* 'datetime' - causes the pico to report back its local date and time, to verify the NTP sync worked

pico[n].py These scripts contain code specific to the tasks I want individual pico modules to perform

secrets.py Contains the various details to connect to Wi-Fi, MQTT and FTP services

trap.py I have a mouse trap instrumented with an infra-red beam to detect mice and a PWM motor to trigger the trap, along with a magnetic reed switch to detect when the trap is closed. This module handles all of that.

generate_shar256.sh Shell script to run on the Raspberry Pi hosting the FTP repositiory; generates text files containing the names of each python module and the SHA256 checksum of them. These text files are pulled down by main.py when it receives a "reload" command so that it can check which modules need updating compared to the local copies.

lib/umqtt/simple.mpy Standard MicroPython MQTT library. Can be installed to a pico using: import mip mip.install("umqtt.simple")

lib/ftplib.py MicroPython compatible ftplib module

utils/ The utils folder contains the following modules:
* am2320.py - module for reporting the temperature and humiditiy from an AM2320 sensor
* blink.py - simple module used for making the on-board LED blink
* ftp.py - wrapper functions to handle pulling back all modified source code from the FTP repositiory
* mqtt.py - wrapper functions for connecting to MQTT and sending messages
* myid.py - returns the name of this pico based on the the machine unique_id property
* ntp.py - used to sync the real time clock with NTP
* sha256.py - used to find the SHA256 checksum of local files when checking which scripts need to be updated from the FTP repository
* wifi.py - used for connecting the pico to the local Wi-Fi

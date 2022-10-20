#Test FTP script
import utils.wifi as wifi

wifi.wlan_connect('pico1')

import utils.ftp as ftp

ftp.cwd('pico')
ftp.get_allfiles(".")
ftp.get_allfiles("utils")
ftp.quit()


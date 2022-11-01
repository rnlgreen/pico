#Python script to get the pico unique ID
from machine import unique_id # type: ignore

picos = {"e6614c311b462739":"pico0", 
         "e6614143288438": "pico1",
         "e661413e7355437": "pico2"
        }
where = {
            "pico0": "study", 
            "pico1": "loft",
            "pico2": "garage"
        }

pico = "unknown"

def get_id():
    global pico
    s = unique_id()
    myid = ""
    for b in s:
        myid = myid + hex(b)[2:]
    print("My ID is {}".format(myid))
    if myid in picos:
        pico = picos[myid]
    return pico

#Python script to get the pico unique ID
from machine import unique_id # type: ignore

picos = {
            "e6614c311b462739":"pico0", 
            "e6614143288438": "pico1",
            "e661413e7355437": "pico2",
            "e6614864d39a8536": "pico3",
            "e6614864d3938134": "pico4",
            "e6614c311b107623": "pico5"
        }
where = {
            "pico0": "study", 
            "pico1": "loft",
            "pico2": "garage",
            "pico3": "kitchen",
            "pico4": "kitchen",
            "pico5": "kitchen"
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

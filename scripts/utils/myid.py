"""Python script to get the pico unique ID"""
from machine import unique_id # type: ignore # pylint: disable=import-error

picos = {
            "e6614c311b462739":"pico0", 
            "e6614143288438": "pico1",
            "e661413e7355437": "pico2",
            "e6614864d39a8536": "pico3",
            "e6614864d3938134": "pico4",
            "e6614c311b107623": "pico5",
            "e6614c311b667426": "pico6",
            "e661413e72d262f": "pico7"
        }
where = {
            "pico0": "lounge", 
            "pico1": "loft",
            "pico2": "garage",
            "pico3": "kitchen",
            "pico4": "kitchen",
            "pico5": "kitchen",
            "pico6": "garage"
        }

pico = "unknown" # pylint: disable=invalid-name

def get_id():
    """Get pico id based on machine ID"""
    global pico # pylint: disable=global-statement
    s = unique_id()
    myid = ""
    for b in s:
        myid = myid + hex(b)[2:]
    print(f"My ID is {myid}")
    if myid in picos:
        pico = picos[myid]
    return pico

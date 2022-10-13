#Python script to get the pico unique ID
import machine

picos = {"e6614c311b462739":"pico1"}

def get_id():
    s = machine.unique_id()
    myid = ""
    for b in s:
        myid = myid + hex(b)[2:]
    print("My ID is {}".format(myid))
    if myid in picos:
        return picos[myid]
    else:
        return "pico-unknown"

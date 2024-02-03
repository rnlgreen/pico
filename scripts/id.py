import machine # pylint: disable=import-error

def id(): # pylint: disable=redefined-builtin
    s = machine.unique_id()
    myid = ""
    for b in s:
        myid = myid + hex(b)[2:]
    print(f"My ID is {myid}")

def main():
    id()

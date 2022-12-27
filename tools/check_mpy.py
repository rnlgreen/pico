#Python script to report the version of an mpy file


releases = {
            "6": "v1.19 and up",
            "5": "v1.12 - v1.18",
            "4": "v1.11",
            "3": "v1.9.3 - v1.10",
            "2": "v1.9 - v1.9.2",
            "0": "v1.5.1 - v1.8.7",
}

with open("simple.mpy", mode='rb') as file: # b is important -> binary
    fileContent = file.read()

v = str(fileContent[1])
s = str(fileContent[2])

print("Version is: {}.{}: {}".format(v,s,releases[v]))

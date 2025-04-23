from __future__ import print_function
import serial
import time
import numpy as np
import csv
from datetime import datetime
import os
from threading import Thread


# TODO test why sometimes devices dont answer on the first call ADD SLEEP
def extractModel(ser, port="COM1"): # Gets model of connected device
    try:
        if ser.is_open:
            print(f"{port}: Model - Connected to port successfully.")
            ser.write(b"en\nsh inv\n ")
            time.sleep(1)
            for i in range(10):
                siw=ser.in_waiting
                if siw > 30:
                    break
                time.sleep(0.5)
            if i==9:
                model= None
            else:
                siw = ser.in_waiting
                output = ser.read(siw).decode("utf-8")
                model = findWordAfterSpecword(output, "PID:")
            if model is None:
                print(f"{port}:Model - Failed to extract from port.")
                return None
            else:
                print(f"{port}:Extracted model: " + model + ".")
                return model
        else:
            print(f"{port}: Model - Failed to open port.")
        return None
    except serial.SerialException:
        print(f"Error: Serial port already in use!") # print(f"Error: (e]")

def extractInterface(ser, port="COM1"): # Gets Interface type of connected device: Gi/Fa
    try:
        if ser.is_open:
            print(f"{port}: Interface - Connected to port successfully.")
            ser.write(b"en\nsh int des\n    ")
            time.sleep(2)
            siw = ser.in_waiting
            output = ser.read(siw).decode('utf-8')
            outputSp = output.split("\r\n")
            interfaceName = ""
            fl = 0
            for line in outputSp:
                if line[:2] == "Fa" or line[:2]== "Gi":
                    interfaceName=line[:2]
                    if fl == 1:
                        break
                    fl = 1
            if interfaceName == "Fa" or interfaceName == "Gi":
                print(f"{port}: Extracted interface: " + interfaceName + ".")
                return interfaceName
            else:
                print(f"{port}: Interface - Failed to extract from port.")
                return None
        else:
            print(f"{port}: Interface - Failed to open port.")

    except serial.SerialException as e:
        print(f"{port}:Error: {e}")


def awaitStartUp(ser): # Waits for device to finish rebooting or copying and
    # resolves if one of the initial steps after startup pops up
    while True:
        ser.write(b"\r\n")
        time.sleep(2)
        siw = ser.in_waiting
        if siw > 8:
            out = ser.read(siw)
            if out[len(out) - 6:] == b"/no]: ":
                ser.write(b"no\n")
                time.sleep(3)
                return 1
            if out[len(out) - 6:] == b"name: ":
                checkLogin(ser, out)
                break
            elif out[len(out) - 1:] == b">":
                break
            elif out[len(out) - 8:] == b"secret: ":
                ser.write(b"JustSkip23\nJustSkip23\n0\n")
                time.sleep(2)
                return 2
            elif out[len(out) - 3:] != b"###":
                if out[len(out) - 1:] == b"#":
                    return 1

def wakeUpAndCheck(ser): # Waits for device to finish rebooting or copying and
    # resolves all the initial steps after startup pops up
    startMark = awaitStartUp(ser)
    siw = ser.in_waiting
    output = ser.read(siw)
    match startMark:
        case 1:
            output = checkConfig(ser,output)
            checkLogin(ser,output)
        case 2:
            output = checkReload(ser, output)
            output = checkConfig(ser, output)
            checkLogin(ser, output)
    enableLogin(ser)
    initDisable(ser)

def checkReload(ser, output = b""): # Checks if the device is awaiting input after reload and resolves it
    if ser.is_open:
        if output == b"":
            ser.write(b"     \r\n\n\n\n\n")
            time.sleep(2)
            siw=ser.in_waiting
            if siw == 0:
                print(f"Reload - No answer.")
            else:
                output = ser.read(siw)
        if output[max(len(output) - 18, 0):] == b"dialog? [yes/no]: ":
            ser.write(b"no\n\n")
            time.sleep(5)
            siw = ser.in_waiting
            output = ser.read(siw)
        return output
    else:
        print(f"Check Reload - Port closed.")


def checkConfig(ser, output=b""): # Checks if the device is in config mode and exits it
    if ser.is_open:
        if output == b"":
            ser.write(b"  \r\n")
            time.sleep(3)
            siw = ser.in_waiting
            output = ser.read(siw)
        if output[max(len(output) - 9, 0):] == b"(config)#":
            ser.write(b"end\n")
            time.sleep(1)
            siw = ser.in_waiting
            output = ser.read(siw)
        return output
    else:
        print(f"Check Config - Port closed.")


def checkLogin(ser, output=b""): # Checks if the device is asking for login credentials and logs in if needed
    if ser.is_open:
        if output == b"":
            ser.write(b"  \r\n")
            time.sleep(2)
            siw = ser.in_waiting
            if siw == 0:
                print(f"Login - No answer.")
            else:
                output = ser.read(siw)
        if output[max(len(output) - 6, 0):] == b"name: ":
            crTxt = open("Docs\\login.txt", "r")
            loginCred = str(crTxt.read()).split("\n")
            crTxt.close()
            username=loginCred[0]
            password=loginCred[1]
            time.sleep(1)
            ser.write(username.encode())
            ser.write(b"\n")
            time.sleep(1)
            ser.write(password.encode())
            ser.write(b"\r\n\n")
            time.sleep(1)
            siw=ser.in_waiting
            output = ser.read(siw)
        return output
    else:
        print(f"Check Login - Port closed.")


def enableLogin(ser): # Puts device into enable mode and logs in if needed
    if ser.is_open:
        ser.write(b"  \r\nen\n")
        time.sleep(1)
        for i in range(10):
            siw = ser.in_waiting
            if siw > 30:
                break
            time.sleep(0.5)
        if i == 9:
            print(f"Enable - No answer.")
        else:
            output = ser.read(siw)
            if output[max(len(output) - 6, 0):] == b"word: ":
                crTxt = open("Docs\\login.txt", "r")
                loginCred = str(crTxt.read()).split("In")
                crTxt.close()
                enablePass=loginCred[2]
                ser.write(enablePass.encode() + b"In\n")
                time.sleep(1)
                siw=ser.in_waiting
                output = ser.read(siw).decode("utf-8")
            return output
    else:
        print(f"Enable - Port closed.")


def initDisable(ser): # Initial disable on new or wiped device to clean up command line
    ser .write(b" conf t\n\nno ip domain lookup \nno logging console\nend\n")


def reboot(ser,port): # Reboots the device and awaits startup
    ser.write(b"reload\n\n\nno\n\n")
    sl = 0.7
    spin = ["", ".", "..", "..."]
    for i in range(30):
        print(f'\r{port}:Rebooting' + spin[i % len(spin)], end= ' ')
        time.sleep(sl)
    print(f'\r{port}:Rebooting...')
    awaitStartUp(ser)

# USED FOR SPECIFIC DISTRIBUTER FOR ADITIONAL INFORMATION
def getTableContents(deviceNumber): # Returns city address and providers of location by number
    addMat = np.array(list(csv.reader(open("Docs\\ExpAdd.csv", "r"), delimiter=";")))
    addMat = np.delete(addMat, 0, axis=0)
    cityNameShort = str(elemOfTableBySubnet(addMat, deviceNumber, 3))
    cityNameShort = cityNameShort.upper()
    cityName = str(elemOfTableBySubnet(addMat, deviceNumber, 1))
    cityName = cityName.upper()
    address = str(elemOfTableBySubnet(addMat, deviceNumber, 2))
    address = address.upper()
    provider1 = str(elemOfTableBySubnet(addMat, deviceNumber, 4))
    provider2 = str(elemOfTableBySubnet(addMat, deviceNumber, 5))
    cont = [cityName, address, cityNameShort, provider1, provider2]
    return cont

def elemOfTableBySubnet(table, sub, col): # Helper funct for getTableContents
    for row in table:
        if int(row[0]) == int(sub):
            return row[col]
    return None


def checkExistence(deviceNumber): # Checks if location exist by number
    addMat = np.array(list(csv.reader(open("Docs\\ExpAdd.csv", "r"), delimiter=";")))
    if str(deviceNumber) not in addMat:
        return False
    return True


def findWordAfterSpecword(text, word): # Finds word after specific word in string
    words = text.split()
    for i in range(len(words) - 1):
        if words[i] == word:
            wordAfterSpecword = words[i + 1]
            return wordAfterSpecword
    return None


def getTime(): # Returns current time in format needed for clock set
    currentTime = datetime.now()
    formatTime = currentTime.strftime("%H:%M:%S %d %B %Y")
    return formatTime


def getCertList(): # Returns list of certificates we want to delete by name
    listCert = open("Docs\\certList.txt", "r")
    certText =str(listCert.read()).split("\n")
    listCert.close()
    return certText

def checkSM(ser, port): # Checks existence of switch module
    ser.write(b"en\nsh inv\n ")
    time.sleep(2)
    for i in range(10):
        siw = ser.in_waiting
        if siw > 30:
            break
        time.sleep(0.5)
    if i == 9:
        sm = -1
        print(f" {port}:No switch module.")
    else:
        siw = ser.in_waiting
        output = ser.read(siw).decode("utf-8")
        sm= output.find("SM-ES")
    return sm


def onListClick(): # Creates thread that opens list of branch office numbers, cities and addresses
    listThread = Thread(target=threadList()) # TODO test why this freezes GUI
    listThread.start()


def threadList(): # Opens list of branch office numbers, cities and addresses
    os.system("Docs\\ExpAdd.csv")

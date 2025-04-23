import serial
import time
import prFunctions as pr
from threading import Thread


def onRunWipeClick(port, portNumV, manualDisc, deviceModel=""): # Creates a thread that will wipe device
    wipeThread = Thread(target=threadWipe,
                        args=(port, portNumV, manualDisc, deviceModel))
    wipeThread.start()


def threadWipe(port, portNumV, manualDisc, deviceModel): # Thread that checks if the device is awake
    # and that the model is valid before starting wipe
    print(f"-----------{port}:WIPE-----------")
    try:
        ser = serial.Serial(port, baudrate = 9600, timeout = 1)
        pr.wakeUpAndCheck(ser)
        if str(manualDisc) == "1":
            deviceModel = deviceModel + "-" + portNumV
        else:
            deviceModel = pr.extractModel(ser = ser, port=str(port))
        if deviceModel is not None:
            deviceModel = deviceModel.replace("+", "-")
            modelSp = deviceModel.split("-")
            deviceName = modelSp[0]
            wipeDevice(ser = ser, port=str(port), deviceName=deviceName)
        else:
            print(f"{port}: Device model not found.")
        ser.close()
    except serial.SerialException as e:
        print(f"{port}: Error: {e}")
        print(f"------------{port}:WIPE-END------------\n")


def wipeDevice(ser, deviceName, port = "COM1"): # Wipes device, certificates, vlan and switch module (if needed)
    try:
        if ser.is_open:
            sm = pr. checkSM(ser, port)
            if sm!=-1:
                wipeSwitchModule(ser, port = port)
            ser.write(b"en\n\ndelete flash:vlan.dat\n\n\n\n")
            time.sleep(1)
            if deviceName == "C4331" or deviceName == "CISCO2911/K9" or deviceName == "C1111":
                certList = pr.getCertList()
                if len(certList) > 0:
                    for i in range(len(certList)):
                        ser.write(b"delete nvram:" + certList[i].encode() + b"\t\n\n\n\n")
                        time.sleep(2)
            ser.write(b"write erase\n\n\n")
            time.sleep(4)
            print(f"{port}: Wiped.")
            pr.reboot(ser, port)
        else:
            print(f"{port}: Failed to open port.")
    except serial.SerialException as e:
        print(f"{port}: Error: {e}")


def wipeSwitchModule(ser,port): # Wipes switch module
    ser.write(b"service-module gigabitEthernet 1/0 session \n\n")
    time.sleep(2)
    siw = ser.in_waiting
    output = ser.read(siw)
    print(f"{port}: Connected to switch module.")
    pr.checkLogin(ser,output)
    time.sleep(1)
    ser.write(b"\r\n")
    pr.enableLogin(ser)
    ser.write(b"\ndelete flash:vlan.dat\n\n\n")
    time.sleep(1)
    ser.write(b"write erase\n\n\n")
    time.sleep(3)
    pr.reboot(ser, port)
    ser.write(b"\x1e") #CTRL + SHIFT + 6
    time.sleep(1)
    ser.write(b"x")
    time.sleep(0.5)
    ser.write(b"disconnect\n\n\n")
    time.sleep(0.5)
    print(f"{port}: Disconnected from switch module.")

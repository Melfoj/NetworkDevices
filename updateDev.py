import serial
import time
import prFunctions as pr
from threading import Thread


def onRunUpdateClick(port, portNumV, manualDisc, deviceModel): # Creates a thread that will update device IOS
    updateThread = Thread(target=threadUpdate,
    args=(port, portNumV, manualDisc, deviceModel))
    updateThread.start()


def threadUpdate(port, portNumV, manualDisc, deviceModel = ""): # Thread that checks if the device is awake
    # and that the model is valid before starting update
    print(f"--{port}:UPDATE--")
    try:
        ser = serial.Serial(port, baudrate = 9600, timeout=1)
        pr.wakeUpAndCheck(ser)
        if str(manualDisc) == "1":
            deviceModel = deviceModel + "-" + portNumV
        else:
            deviceModel =pr.extractModel(ser, port=str(port))
        if deviceModel is not None:
            deviceModel = deviceModel.replace("+", "-")
            modelSp = deviceModel.split("-")
            if modelSp[0] == "WS":
                modelSp.pop(0)
            deviceName = modelSp[0]
            ser = update(ser=ser, port=str(port), deviceName = deviceName)
        else:
            print(f"{port}: Device model not found.")
        ser.close()
    except serial.SerialException:
        print(f"Error: Serial port already in use!")#print(f"Error: (e)")
        print(f"-----------{port}:UPDATE-END-----------\n")


def update(ser, deviceName, port = "COM1"): # Sends files via usb or console cable depending on the device model
    try:
        if ser.is_open:
            print(f"(port): Update - Connected to port successfully.")
            ser.write(b"\n")
            time.sleep(1)
            ser.write(b"en\n")
            usbSupport = True
            # Determine device type and copy appropriate IOS versions
            match deviceName:
                case 'C1000' | 'C1000FE':
                    recVer = "c1000-universalk9-mz.152-7.E9.bin" # or other versions
                    UText = "\nen\n\ncopy usbflash0:" + recVer + " flash\n\n\n\n"
                case 'C1111 ':
                    recVer="c1100-universalk9.17.09.04a.SPA.bin" # or other versions
                    UText = "\nen\n\ncopy usb0:" + recVer + " flash\n\n\n\n"
                case 'CISCO2911/K9':
                    print("Model not supported yet.")
                    usbSupport = False
                case 'C2960':
                    print("Model not supported yet.")
                    usbSupport = False
                    recVer="c2960-lanlitek9-mz.152-7.E9.bin" # or other versions
                case 'C2960X':
                    recVer = "c2960x-universalk9-mz.152-4.E8.bin" # or other versions
                    UText = "\nen\n\ncopy usbflash0:" + recVer + " flash\n\n\n\n"
                case 'C881' | 'C881G':
                    recVer = "c880data-universalk9-mz.153-3.M4.bin" # or other versions
                    UText = "\nen\n\ncopy usbflash0" + recVer + " flash\n\n\n\n"
                case 'C4331' :
                    recVer="isr4300-universalk9.16.03.07.SPA.bin" # or other versions
                    UText = "\nen\n\ncopy usb0:" + recVer + " flash\n\n\n\n"
                case _:
                    print(f"({port}:Model not supported")
                    usbSupport = False
            if usbSupport:
                ser.write(UText.encode())
                sl=0.7
                spin=["", ".", "..", "..."]
                for i in range(30):
                    print(f'\r{port}: Copying'+spin[i % len(spin)], end='')
                    time.sleep(sl)
                print(f"\r{port}:Copying...")
                pr.awaitStartUp(ser)
                ser.write(b"\ndir\n         ")
                time.sleep(3)
                siw = ser.inwaiting
                dirText = ser.read(siw).decode("utf-8")
                dirText = dirText.split("\r\n")
                checkCopy = False
                for line in dirText:
                    if line[len(line) - 20:] == recVer[len(recVer) - 20:]:
                        checkCopy=True
                        break
                if checkCopy:
                    print(f"(port):Copying successful.")
                    ser .write(b"\nsh run inc boot sys\n")
                    # time.sleep(1)
                    # siw = ser.in_waiting
                    # output = ser.read(siw).decode("utf-8")
                    # output = output.split("\r\n")
                    # output = output[2] # TODO test without - c1000ok,2960Xok,
                    UText = "conf t\n\nboot system flash:" + recVer + "\n\n\nend\nwrite\n\n"
                    ser.write(UText.encode())
                    time.sleep(1)
                    # if output != ""
                    #   ser.write(b"\nno boot system flash:" + output.encode() + b"\n\n")
                    #   time.sleep(1)
                    pr.reboot(ser, port)
                else:
                    print(f"{port}: Update - failed to copy.")
            # else:
                # ser .write(b"conf t\nline console 0\nspeed 115200")
                # ser.close()
                # ser = serial.Serial(port, baudrate=115200, timeout=1)
                # ser.write(b"end\nxmodem: flash:"+ recver.encode() t b"\n")#TODO test
                # pr.awaitStartUp(ser)
                # ser.write(b"conf t\nboot flash:" + recver.encode() + b"\n")
                # time.sleep(2)
                # ser.write(b"line console 0\nspeed 9600\n")
                # ser.close()
                # ser = serial.Serial(port, baudrate=9600, timeout=1)
                # ser.write(b"wr\n")
                # time.sleep(2)
                # pr.reboot(ser, port)
        else:
            print(f"{port}: Update - Failed to open port.")
        return ser
    except serial.SerialException as e:
        print(f"(port):Error: {e}")

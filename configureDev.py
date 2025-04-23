import serial
import time
import prFunctions as pr
import extractRouterConf as rc
import tkinter.messagebox
from threading import Thread
import generateFiles as gen
import os


switchModels=["C1000", "C1000FE", "C2960X", "C2960"]
routerModels=["C1111", "CISCO2911/K9", "C881", "C881G", "C4331"]

def onRunConfigureClick(port, portNumV, deviceNumber, manualDisc, extraCommands="", deviceModel=""): # Assures that
    # the location(by number) exists and creates a thread to configure device
    print(f"---------------{port}:CONFIGURE---------------")
    if deviceNumber == "":
        print(f"NumberBox is empty.\n---------------{port}:CONFIGURE-END---------------\n")
        tkinter.messagebox.showerror("Error", "Please add number.")
    elif not pr.checkExistence(deviceNumber.zfill(3)):
        print(f"Number doesn't exist.\n---------------{port}:CONFIGURE-END---------------\n")
        tkinter.messagebox.showerror("Error", "Number doesn't exist ")
    else:
        try:
            deviceNumber = deviceNumber.zfill(3)
            runThread = Thread(target=threadRun,
                args=(port, portNumV, deviceNumber, manualDisc, extraCommands, deviceModel))
            runThread.start()
        except serial.SerialException:
            print(f"Error: Serial port already in use!")#print(f"Error:fe)")


def threadRun(port, portNumV, deviceNumber, manualDisc, extraCommands="", deviceModel=""): # Thread that assures that
    # the device is active and gets manual or automatic device discovery
    ser = serial.Serial(port, baudrate=9600, timeout=1)
    pr. wakeUpAndCheck(ser)
    if str(manualDisc) == "1":
        deviceModel = deviceModel.upper()
        if deviceModel in ["C2911", "C2911/K9"]:
            deviceModel = "CISCO2911/K9"
        deviceModel = deviceModel + "-" + portNumV
    else:
        deviceModel =pr.extractModel(ser=ser, port=str(port))

    delay = 1
    if deviceModel is not None:
        deviceModel = deviceModel.replace("+", "-")
        modelSp =deviceModel.split("-")
        if deviceModel == "CISCO2911/K9":
            deviceName = "CISCO2911/K9"
            portNum = 2
            delay = 2
        else:
            if modelSp[0] == "WS":
                modelSp.pop(0)
            deviceName = modelSp[0]
            portNum = modelSp[1]
            portNum = int("".join(c for c in portNum if c.isdecimal()))
        interfaceType = pr.extractInterface(ser=ser, port=str(port))
        setup(ser=ser,
            port=str(port),
            deviceNumber=deviceNumber,
            deviceName=deviceName,
            portNum=portNum,
            interfaceType=interfaceType,
            extraCommands=extraCommands,
            delay= delay)
    else:
        print("Device model not found.")
    ser.close()
    print(f"---------------{port}:CONFIGURE-END---------------\n")


def setup(ser, deviceNumber, deviceName, portNum, interfaceType, extraCommands, port="COM1", delay = 1): # Splits devices
    # into switches and routers, starts configuration for both + certification for routers + Switch module setup if needed
    try:
        if ser.is_open:
            print(f"(port):Setup - Connected to port successfully.")

            # Sending command to the switch
            ser.write(b"\n")
            time.sleep(1)
            confDev=[]

            if deviceName in switchModels: #SWITCH
                configName="Switch_"+deviceNumber
                confDev=switchConfigure(deviceNumber=deviceNumber,
                    portNum=portNum,
                    interfaceType=interfaceType,
                    deviceName=deviceName)
                time.sleep(1)
                sm=-1
            elif deviceName in routerModels: #ROUTER
                sm=pr.checkSM(ser,port)
                configName = "Router_" + deviceNumber
                confDev=routerConfigure(deviceNumber=deviceNumber,
                    portNum=portNum,
                    interfaceType=interfaceType,
                    deviceName=deviceName)
                portVer = "0/0/0"
                if deviceName == "CISCO2911/K9":
                    portVer = "0/1"
                time.sleep(1)
                certText=routerCertificate(interfaceType=interfaceType,
                    portVer=portVer,
                    deviceNumber=deviceNumber)

            print(f"{port}: Certification initiated.")
            pr.enableLogin(ser)
            ser.write(b"conf t\n")
            for i in range(len(certText)-2):
                ser.write(certText[i].encode())
                time.sleep(1)
            print(f"{port}: Plug network cable into port Gi{portVer}.")
            tkinter.messagebox.showerror("Paused", f"Plug network cable into port Gi{portVer}.")
            print(f"{port}: Connecting to network...")
            time.sleep(30) # TODO test time to connect - lower if possible
            ser.write(certText[-2].encode())
            print(f"{port}: Unplug network cable from port Gi{portVer}.")
            tkinter.messagebox.showerror("Paused", f"Unplug network cable from port Gi{portVer}.")
            time.sleep(1)
            ser .write(certText[-1].encode)
            time.sleep(1)
            ser.write(b"\nwr\n\n")
            time.sleep(3)
            pr.reboot(ser,port)
            pr.enableLogin(ser)
            ser.write(b"conf t\n")

        # if extraCommands != ""
        # print(f"--(port):Extra commands--")
        # print(extraCommands)
        # print(f"--(port):Extra commands end--")
        fullConfig = ""
        if confDev is not []:
            spin = ["", ".", "..", "..."]
            for i in range(len(confDev)):
                if confDev[i]!="":
                    print(f"\r{port}:Configuring device" + spin[i % len(spin)], end=' ')
                    ser.write(confDev[i]. encode())
                    time.sleep(delay)
                    fullConfig += confDev[i]#+"\n"
            print(f'\r{port}: Configuring device...')
            if extraCommands != "":
                ser.write(extraCommands.encode())
                time.sleep(delay)
                fullConfig = fullConfig + "\n" + extraCommands
            ser.write(b"In\nend\nwr\n\n\n")
            time.sleep(delay*3)

        path = "Output\\Exp_" + str(deviceNumber)
        if not os.path.exists(path):
            os.mkdir(path)

        # Create config file
        f = open("Output\\Exp_" + str(deviceNumber) +"\\"+ configName + ".txt", "a")
        f.write(fullConfig)
        f.close()

        if sm != -1:
            smText = smConfigure(deviceNumber=deviceNumber)
            pr.enableLogin(ser)
            ser.write(b"conf t\n")
            ser.write(b"int gi1/0\nno shu\nip address 1.1.1.1 255.255.255.0\nint emb0/0\nno shu\nend\nconf t"
                b"\nline 67\nno activation-character\nno exec\ntransport preferred none\ntransport input all"
                b"\ntransport output all\nstopbits 1\nflowcontrol software\nend\n")
            time.sleep(1)
            ser.write(b"service-module gigabitEthernet 1/0 session\n")
            time.sleep(1)
            siw = ser.in_waiting
            output=ser.read(siw)
            print(f"{port}:Configuring switch module.")
            # print(output.decode("utf-8"))
            pr.checkLogin(ser, output)
            pr.enableLogin(ser)
            # print(output.decode("utf-8"))
            pr.checkLogin(ser, output)
            pr.enableLogin(ser)
            ser.write(b"conf t\n")
            for i in range(len(smText)):
                ser.write(smText[i] .encode())
                time.sleep(1)
            ser.write(b"\n\nend\nwr\n\n\n")
            time.sleep(3)
            ser.write(b"\x1e") # CTRL + SHIFT + 6
            time.sleep(1)
            ser.write(b"x")
            time.sleep(0.5)
            ser.write(b"disconnect\n\n\n")
            time.sleep(0.5)

        else:
            print(f"{port}:Setup - Failed to open port.")
    except serial.SerialException:
        print(f"Error: Serial port already in use!")#print(f"Error: (e)")


# FOR SPECIFIC USECASE
# def switchConfigure(deviceNumber,portNum, interfaceType, deviceName): # Returns configuration for
#     # switch with needed changes to the base configuration
#     addMat = pr.getTableContents(deviceNumber=deviceNumber)
#     spaceNumber = 57 - len(addMat[0]) - len(addMat[1]) # custom banner settings
#     spaceL = int(spaceNumber/2)
#     spaceR = int(spaceNumber/2) + spaceNumber % 2
#     portVer = "1/"
#     if interfaceType == "Gi":
#         trunkPort = str(portNum)
#     elif interfaceType == "Fa":
#         trunkPort = "2"
#     if deviceName == "C2960":
#         portVer = ""
#     blankSetup = open("Docs\\switchSetup.txt", "r")
#     switchText = (str(blankSetup.read())
#         .replace("???nameVtp???", addMat[0] + "_" + str(deviceNumber))
#         .replace("???hostname???", "s_"+addMat[2] +"_" + str(deviceNumber))
#         .replace("???portNum???", str(portNum)))
#     switchText = ((switchText
#                   .replace("???locNum???", str(deviceNumber)))
#                   .replace("???cityName???"," "*spaceL + addMat[0].upper())
#                   .replace("???address???", addMat[1].upper()+" - SW" +" "*spaceR))
#     switchText = (((switchText
#                   .replace("???interfaceType???", interfaceType))
#                   .replace("???1/???", portVer))
#                   .replace("???trunkPort???", trunkPort))
#     if deviceName == "C2960":
#         switchText = switchText.replace("edge", "")
#     switchText = switchText.split("!----------------------------------------------------------") # split delimiter
#     blankSetup.close()
#     if deviceName == "C2960":
#         del switchText[6]
#     else:
#         del switchText[5]
#     return switchText


def switchConfigure(deviceNumber,portNum, interfaceType, deviceName): # Returns configuration for
    # switch with needed changes to the base configuration
    portVer = "1/"
    if interfaceType == "Gi":
        trunkPort = str(portNum)
    elif interfaceType == "Fa":
        trunkPort = "2"
    if deviceName == "C2960":
        portVer = ""
    blankSetup = open("Docs\\switchSetup.txt", "r")
    switchText = (str(blankSetup.read())
        .replace("???hostname???", "s_" + str(deviceNumber))
        .replace("???portNum???", str(portNum)))
    switchText = (((switchText
                  .replace("???interfaceType???", interfaceType))
                  .replace("???1/???", portVer))
                  .replace("???trunkPort???", trunkPort))
    switchText = switchText.split("!----------------------------------------------------------") # split delimiter
    blankSetup.close()
    return switchText


# FOR SPECFIC USECASE
# def routerConfigure(deviceNumber,portNum, interfaceType, deviceName): # Returns configuration for
#     # router with needed changes to the base configuration
#     addMat = pr.getTableContents(deviceNumber=deviceNumber)
#     spaceNumber = 74 - len(addMat[0]) - len(addMat[1])
#     spaceL = int(spaceNumber / 2)
#     spaceR= int(spaceNumber / 2) + spaceNumber % 2
#     routerProd=rc.extractRouterConfig(deviceNumber=deviceNumber.lstrip("0"))
#     if deviceName == "CISCO2911/K9":
#         blankSetup = open("Docs\\routerSetup2911.txt", "r")
#     else:
#         blankSetup = open("Docs\\routerSetup.txt", "r")
#     routerText = str(blankSetup.read())
#     routerText = routerText.replace("???nameVtp???", addMat[0] + str(deviceNumber)).replace("???hostname???", "r_" + addMat[2] + "_" + str(deviceNumber))
#     routerText = routerText.replace("???portNum???", str(portNum)).replace("???locNum???", str(deviceNumber)).replace("???cityName???" + " "*spaceL + addMat[0].upper())
#     routerText = routerText.replace("???address???", addMat[1].upper() +" "*spaceR).replace("???interfaceType???", interfaceType)

#     routerText=routerText.split("!----------------------------------------------------------")
#     blankSetup.close()
#     routerProd[1]=routerProd[1].replace("GigabitEthernet0/1", "GigabitEthernet0/0/0")
#     routerProd[1]=routerProd[1].replace("GigabitEthernet0/2", "GigabitEthernet0/0/1")

#     routerText[5]=routerText[5].replace("???policyMap???", routerProd[0])
#     routerText[7]=routerText[7].replace("???tunnels???", routerProd[1])
#     routerText[8]=routerText[8].replace("???Gi0???", routerProd[2])
#     routerText[9]=routerText[9].replace("???Gi1???", routerProd[3])

#     if routerProd[4] == "":
#         routerText[11]= ""
#     else:
#         routerText[11]=routerText[11].replace("???Vlan6???", routerProd[4])

#     if routerProd[5]=="":
#         routerText[12]=""
#     else:
#         routerText[12]=routerText[12].replace("???Vlan8???", routerProd[5])

#     routerText[13]=routerText[13].replace("???neighborList???", routerProd[6])
#     routerText[14]=routerText[14].replace("???ipRoute???", routerProd[7])
#     routerText[15] = routerText[15].replace("???ipAccessListPermits???", routerProd[8])
#     routerText[18] = routerText[18].replace("???routeMap???", routerProd[9])
#     spaceSIP = 77 - len(routerProd[10])
#     routerText[22] = routerText[22].replace("???sipTrunk???", routerProd[10] + " "*spaceSIP)
#     spaceADSL=68 - len(routerProd[11])
#     routerText[22] = routerText[22].replace("???adslSec???", routerProd[11]+ " ADSL+SEC" + " "*spaceADSL)

#     provider1 = routerProd[2]
#     provider2 = routerProd[3]
#     if provider1 !="":
#         provider1 = provider1.split("\n")
#         provider1 = provider1[1]
#         provider1 = provider1.split(" ")
#         provider1 = provider1[-2]
#     if provider2 !="":
#         provider2 = provider2.split("\n")
#         provider2 = provider2[1]
#         provider2 = provider2.split(" ")
#         provider2 = provider2[-2]

#     gen.generateAll(deviceNumber,addMat[0],addMat[1],provider1,provider2)
#     return routerText


def routerConfigure(deviceNumber,portNum, interfaceType, deviceName): # Returns configuration for
    # router with needed changes to the base configuration
    routerProd = rc.extractRouterConfig(deviceNumber=deviceNumber.lstrip("0"))
    if deviceName == "CISCO2911/K9": # The 2911 often has older commands
        blankSetup = open("Docs\\routerSetup2911.txt", "r")
    else:
        blankSetup = open("Docs\\routerSetup.txt", "r")
    routerText = str(blankSetup.read())
    routerText = routerText.replace("???nameVtp???", "VTP_" + str(deviceNumber)).replace("???hostname???", "r_" + str(deviceNumber))
    routerText = routerText.replace("???portNum???", str(portNum)).replace("???locNum???", str(deviceNumber)).replace("???interfaceType???", interfaceType)

    routerText=routerText.split("!----------------------------------------------------------")
    blankSetup.close()
    return routerText


def routerCertificate(interfaceType, portVer, deviceNumber): # Returns certification for
    # routers with needed changes to the base configuration
    hostname = "r_" + str(deviceNumber)
    currentTime = pr.getTime()
    blankCertificate = open("Docs\\routerCertificate.txt" "r")
    certText = (str(blankCertificate.read())
                .replace("???hostname???", hostname)
                .replace("???interfaceType???", interfaceType)
                .replace("???portVer???", portVer)
                .replace("???currentTime???", currentTime))
    certText = certText.split("!----------------------------------------------------------")
    blankCertificate.close()
    return certText


def smConfigure(deviceNumber): # Returns configuration for switch module with needed changes to the base configuration
    blankSetup = open("Docs\\smSetup.txt", "r")
    smText = ((blankSetup.read())
              .replace("???nameVtp???", "VTP_" + str(deviceNumber))
              .replace("???hostname???", "s_" + str(deviceNumber))
              .replace("???locNum???", str(deviceNumber)))
              
    smText = smText.split("!----------------------------------------------------------")
    blankSetup.close()
    # print(f"--\n{port}:Switch Module Config--\n")
    # for i in range(len(smText)):
    #   print(smText[i])
    # print(f"\n--(port):Switch Module Config end--\n")
    return smText

from netmiko import ConnectHandler
import prFunctions as pr


def extractRouterConfig(deviceNumber): # Connects to production device that we are preparing replacement for
    # and extracts parts of configuration that are location dependent
    netConnect = ConnectHandler(device_type="cisco_ios", host="1.1.1."+str(int(deviceNumber)),#ROUTER made up add
    username="cisco", password="cisco", secret="cisco")
    netConnect.enable()
    deviceModel = netConnect.send_command("sh inv")
    deviceModel = pr.findWordAfterSpecword(deviceModel, "PID:")
    outputRun = netConnect.send_command("sh run")
    outputSection = []
    startIndex=[0]*12
    endIndex=[0]*12

    # SPECIFIC CASE
    match deviceModel:
        case "CISCO2911/K9":
            startIndex[0] = outputRun.find("policy-map")
            endIndex[0] = outputRun. find("policy-map MARKIRANJE", max(0, startIndex[0])) - 1

            startIndex[1] = outputRun.find("interface Tunnel", max(0, endIndex[0]))
            endIndex[1] = outputRun.find(": interface Embedded", max(0, startIndex[1]))

            startIndex[2] - outputRun.find("interface GigabitEthernet0/1", max(0, endIndex[1])) + 28
            endIndex[2] = outputRun.find("load-interval", max(0, startIndex[2])) - 1
            if endIndex[2] < 0:
                startIndex[2] = outputRun.find("interface GigabitEthernet0/1", max(0, endIndex[1]))

            startIndex[3] = outputRun.find("interface GigabitEthernet0/2", max(0, endIndex[2])) + 28
            endIndex[3] =outputRun.find("load-interval", max(0, startIndex[3])) -1
            if endIndex[3] < 0:
                endIndex[3] = outputRun.find("no ip proxy-arp", max(0, startIndex[3])) - 1

            startIndex[4] = outputRun.find("dot1Q 6", max(0, endIndex[3]))
            endIndex[4] = outputRun.find("ip access-group", max(0, startIndex[4])) - 1

            startIndex[5] = outputRun.find("dot1Q 8", max(0, endIndex[4]))
            endIndex[5] = outputRun.find("ip access-group", max(0, startIndex[5])) -1

        case _:
            startIndex[0] = outputRun.find("policy-map")
            endIndex[0] = outputRun.find("policy-map mark", max(0, startIndex[0])) -1

            startIndex[1] = outputRun.find("interface Tunnel", max(0, endIndex[0]))
            endIndex[1] = outputRun.find("interface Gigabit", max(0, startIndex[1])) - 1

            startIndex[2] = outputRun.find("interface GigabitEthernet0/0/0", max(0, endIndex[1])) + 31
            endIndex[2] =outputRun.find("load-interval", max(0, startIndex[2])) - 1
            if endIndex[2] < 0:
                endIndex[2] - outputRun.find("no ip proxy-arp", max(0, startIndex[2])) - 1

            startIndex[3] = outputRun.find("interface GigabitEthernet0/0/1", max(0, endIndex[2])) + 31
            endIndex[3] = outputRun.find("load-interval", max(0, startIndex[3])) - 1
            if endIndex[3] < 0:
                endIndex[3] = outputRun.find("no ip proxy-arp", max(0, startIndex[3]))

            startIndex[4]= outputRun.find("description VLAN2", max(0, endIndex[3]))
            endIndex[4]= outputRun.find("ip nbar", max(0, startIndex[4])) - 1

            startIndex[5]= outputRun.find("description VLAN3", max(0, endIndex[4]))
            endIndex[5] = outputRun.find("ip nbar", max(0, startIndex[5])) - 1

    startIndex[6] = outputRun.find("router bgp", max(0, endIndex[5]))
    endIndex[6] = outputRun.find("ip local policy", max(0, startIndex[6])) - 1

    startIndex[7] = outputRun.find("ip route", max(0, endIndex[6]))
    endIndex[7]= outputRun.find("ip tacacs", max(0, startIndex[7])) - 1

    startIndex[8]= outputRun.find("ip access-list", max(0, endIndex[7]))
    endIndex[8] - outputRun.find("ip access-list extended vid", max(0, startIndex[8])) - 1

    startIndex[9] = outputRun.find("route-map", max(0, endIndex[8]))
    endIndex[9] = outputRun.find("route-map IBGP", max(0, startIndex[9]))

    startIndex[10] = outputRun.find("ADSL:", max(0, endIndex[9]))
    if startIndex[10] < 0:
        startIndex[10] = outputRun.find("TRUNK:", max(0, endIndex[9]))
    endIndex[10] = outputRun.find(" ", max(0, startIndex[10] + 17)) - 1

    startIndex[11] = outputRun. find("ANALOG:", max(0, endIndex[10]))
    endIndex[11] =outputRun.find("", max(0, startIndex[11] + 17)) - 1

    for i in range(12):
        if startIndex[i] > 0 and endIndex[i] > 0:
            outputSection.append(outputRun[startIndex[i]:endIndex[i]])
        else:
            outputSection.append("")
        match i:
            case 0:
                print(f"{deviceNumber}:Missing policy map.")
            case 1:
                print(f"{deviceNumber}:Missing tunnels.")
            case 2:
                print(f"{deviceNumber}:Missing Gi1 ip and description.")
            case 3:
                print(f"{deviceNumber}:Missing Gi2 ip and description.")
            case 4:
                print(f"{deviceNumber}:Missing Vlan2.")
            case 5:
                print(f"{deviceNumber}:Missing Vlan3.")
            case 6:
                print(f"{deviceNumber}:Missing BGP.")
            case 7:
                print(f"{deviceNumber}:Missing ip route.")
            case 8:
                print(f"{deviceNumber}:Missing access group.")
            case 9:
                print(f"{deviceNumber}:Missing route map.")
            case 10:
                print(f"{deviceNumber}:Missing SIP number.")
            case 11:
                print(f"{deviceNumber}:Missing Analog number.")

    # print("In\n -----Policy,Tunnel, Gi1, Gi2, dot1Q 6, dot1Q 8,BGP, Ip route, access-group, route-map
    # for i in range(len(outputSection)):
    #   print (outputSection[i])
    #   print("--------------------------")
    return outputSection

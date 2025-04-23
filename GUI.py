from tkinter import *
from tkinter import ttk
import tkinter.messagebox
import updateDev as ud
import configureDev as cd
import wipeDev as wd
import prFunctions as pr


# Main application Size and Appearance
winWidth = "275" # 478"
winHeight = "170"
expWinHeight = "490"
mainWindow = Tk()
mainWindow.title("TLC")
mainWindow.geometry(winWidth+"x"+winHeight)
mainWindow.resizable(False, False)


checkVar = tkinter.IntVar()
radioCom = tkinter.StringVar()


def toggleAdvancedOptions(): # Expands GUI to show advanced options
    if advancedFrame.winfo_viewable():
        advancedFrame.grid_remove()
        expandButton.config(text="Show Advanced")
        mainWindow.geometry(winWidth+"x"+winHeight)
    else:
        advancedFrame.grid()
        expandButton.config(text="Hide Advanced")
        mainWindow.geometry(winWidth+"x"+expWinHeight)

listButton = ttk.Button(mainWindow, text="List", width=6, command=lambda: pr.onListClick())
listButton.grid(row=0, column=1, padx=5, pady=5, sticky=tkinter.E) # Lists branch office numbers, cities and addresses


labelNumber = tkinter.Label(mainWindow, text="Num:")
labelNumber.grid(row=0, column=2, padx=5, pady=5, sticky=tkinter.NW)


textboxNumber = tkinter.Text(mainWindow, height=1, width=3) # Input for number of branch office
# for which the device is being configured
textboxNumber.grid(row=0, column=3, padx=5, pady=5)


runUpdateButton = ttk.Button(mainWindow, text="Update", width=12, command=lambda :ud.onRunUpdateClick(
    port= radioCom.get(),
    portNumV= combo.get(),
    manualDisc= checkVar.get(),
    deviceModel= textboxModel.get(1.0, "end-1c"))) # Update device IOS
runUpdateButton.grid(row=1, column=0, columnspan=2, padx=5, pady=20, sticky=tkinter.E)


wipeButton = ttk.Button(mainWindow, text="Wipe", width=12, command=lambda :wd.onRunWipeClick(
    port= radioCom.get(),
    portNumV= combo.get(),
    manualDisc= checkVar.get(),
    deviceModel= textboxModel.get(1.0, "end-1c"))) # Wipe device
wipeButton.grid(row=1, column=2, columnspan=2, padx=5, pady=20, sticky=tkinter.E)


runConfigureButton =ttk.Button(mainWindow, text="Configure", width=12, command=lambda :cd.onRunConfigureClick(
    port= radioCom.get(),
    portNumV= combo.get(),
    deviceNumber= textboxNumber.get(1.0, "end-1c"),
    manualDisc= checkVar.get(),
    deviceModel= textboxModel.get(1.0, "end-1c"),
    extraCommands= textboxCommands.get(1.0, "end-1c")))
runConfigureButton.grid(row=1, column=4, padx=5, pady=20, sticky=tkinter.E)#Configure device


# terminalList=Listbox(mainWindow, width=32, height=7)
# terminalList.grid(row-1, column-5, rowspan=3, sticky=NSEW)


radioCom.set("COM1") # Port selection


radioC1 = ttk.Radiobutton(mainWindow, text="COM1", variable=radioCom, value="COM1")
radioC1.grid(row=2, column=1, padx=5, pady=5, sticky=tkinter.W) # Port selection


radioC2 = ttk.Radiobutton(mainWindow, text="COM2", variable=radioCom, value="COM2")
radioC2.grid(row=3, column=1, padx=5, pady=5, sticky=tkinter.W) # Port selection


# Button to toggle the advanced options
expandButton =ttk.Button(mainWindow, text="Show Advanced",command=toggleAdvancedOptions)
expandButton.grid(row=3, column=3, columnspan=2, padx=5, pady=5) # Expand GUI for advanced options (initially hidden)


advancedFrame = tkinter.Frame(mainWindow)
advancedFrame.grid(row=4, column=0, columnspan=5, pady=5, padx=5)#columnspan-6
advancedFrame.grid_remove() # Hide the frame initially


manualCheckbox = tkinter.Checkbutton(advancedFrame, text="Manual discover", variable = checkVar) # Discover device manually
manualCheckbox.grid(row=6, column=1, columnspan=2, padx=5, pady=5)


labelName = tkinter.Label(advancedFrame, text="Model:")
labelName.grid(row=7, column=1, padx=5, pady=5, sticky=tkinter.W)


textboxModel = tkinter.Text(advancedFrame, width=15, height=1) # Model of device - manual
textboxModel.grid(row=7, column=2, columnspan=2, padx=5, pady=5)


combo=ttk.Combobox(advancedFrame, values=["4p","8p","24p","48p"], width=4) # Port number of device - manual
combo.grid(row=7, column=4, columnspan=1, padx=5, pady=5)


labelCommands = tkinter.Label(advancedFrame, text="ADD EXTRA COMMANDS:")
labelCommands.grid(row=8, column=1, columnspan=3, padx=5, pady=5, sticky=tkinter.W)


textboxCommands = tkinter.Text(advancedFrame, width = 32, height=13) # Extra commands on top of base configuration
textboxCommands.grid(row=9, column=0, columnspan=6, padx=0, pady=5) # width = 58

# GUI event loop
mainWindow.mainloop()

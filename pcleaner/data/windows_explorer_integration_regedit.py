import sys
import winreg
import pyuac


def checkWindows():
    return "win32" in sys.platform


def generateKeys(programPath: str):
    createContextMenuTask(r"\\Directory\\Background\\shell\\", programPath)
    createContextMenuTask(r"\\Directory\\shell\\", programPath)

    createContextMenuSubCommand("Pclean.both", programPath + ' clean "%V" --notify', "Save both masks and cleaned page")
    createContextMenuSubCommand("Pclean.mask", programPath + ' clean -m "%V" --notify', "Save only masks")
    createContextMenuSubCommand("Pclean.clean", programPath + ' clean -c "%V" --notify', "Save only cleaned page")


def createContextMenuTask(path: str, programPath: str):
    currentKey = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, access=winreg.KEY_ALL_ACCESS)

    PcleanKey = winreg.CreateKey(currentKey, "Pcleaner")

    winreg.SetValueEx(PcleanKey, r"Icon", 0, winreg.REG_SZ, programPath)
    winreg.SetValueEx(PcleanKey, r"MUIVerb", 0, winreg.REG_SZ, r'Run Panel Cleaner against this folder')
    winreg.SetValueEx(PcleanKey, r"SubCommands", 0, winreg.REG_SZ, r'Pclean.both;|;Pclean.mask;Pclean.clean;')

    winreg.CloseKey(PcleanKey)
    winreg.CloseKey(currentKey)


def createContextMenuSubCommand(name: str, command: str, description: str):
    currentKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\CommandStore\\shell",
                                access=winreg.KEY_ALL_ACCESS)

    cleanTaskKey = winreg.CreateKey(currentKey, name)

    winreg.SetValueEx(cleanTaskKey, r"MUIVerb", 0, winreg.REG_SZ, description)

    commandKey = winreg.CreateKey(cleanTaskKey, "command")

    winreg.SetValueEx(commandKey, "", 0, winreg.REG_SZ, command)

    winreg.CloseKey(commandKey)
    winreg.CloseKey(cleanTaskKey)
    winreg.CloseKey(currentKey)


def deleteKeys():
    deleteSubCommandKey("Pclean.both")
    deleteSubCommandKey("Pclean.clean")
    deleteSubCommandKey("Pclean.mask")

    deleteContextMenuKey()


def deleteContextMenuKey():
    try:
        currentKey = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "\\Directory\\Background\\shell\\Pcleaner",
                                    access=winreg.KEY_ALL_ACCESS)

        winreg.DeleteValue(currentKey, "MUIVerb")
        winreg.DeleteValue(currentKey, "Icon")
        winreg.DeleteValue(currentKey, "SubCommands")

        winreg.DeleteKey(currentKey, "")
        winreg.CloseKey(currentKey)

        currentKey = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "\\Directory\\shell\\Pcleaner",
                                    access=winreg.KEY_ALL_ACCESS)

        winreg.DeleteValue(currentKey, "MUIVerb")
        winreg.DeleteValue(currentKey, "Icon")
        winreg.DeleteValue(currentKey, "SubCommands")

        winreg.DeleteKey(currentKey, "")
        winreg.CloseKey(currentKey)
    except FileNotFoundError:
        return


def deleteSubCommandKey(keyName: str):
    try:
        currentKey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                    r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\CommandStore\\shell\\" + keyName,
                                    access=winreg.KEY_ALL_ACCESS)

        commandKey = winreg.OpenKey(currentKey, "command")

        winreg.DeleteKey(commandKey, "")
        winreg.CloseKey(commandKey)

        winreg.DeleteValue(currentKey, "MUIVerb")
        winreg.DeleteKey(currentKey, "")
        winreg.CloseKey(currentKey)
    except FileNotFoundError:
        return


if __name__ == "__main__":
    if len(sys.argv) == 3:

        if sys.argv[1] == "create" or sys.argv[1] == "delete":
            if not pyuac.isUserAdmin():
                print("Re-launching as admin!")
                pyuac.runAsAdmin()
            else:
                if sys.argv[1] == "create":
                    generateKeys(sys.argv[2])
                elif sys.argv[1] == "delete":
                    deleteKeys()
        else:
            print("Invalid command, please enter create or delete followed by the path of the Panel Cleaner Exe")
            sys.exit(1)
    else:
        print("Invalid command, please enter create or delete followed by the path of the Panel Cleaner Exe")
        sys.exit(1)

    print("Finished")

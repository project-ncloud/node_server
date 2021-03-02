import subprocess
from os import system
import platform


def isAlive():
    return True if isProcessAlive("smbd") else False

def wake():
    if platform.system() != 'Windows':
        ret = system("sudo systemctl start smbd")
        return True if ret == 0 else False
    else:
        return True


def kill():
    if platform.system() != 'Windows':
        ret = system("sudo systemctl stop smbd")
        return True if ret == 0 else False
    else:
        return True


def isProcessAlive(processName:str):
    if platform.system() != 'Windows':
        p =  subprocess.Popen(["systemctl", "is-active",  processName], stdout=subprocess.PIPE)
        (output, err) = p.communicate()
        output:str = output.decode('utf-8')
        return True if output.strip().lower() == "active" else False
    else:
        return True


def getCurrentUser():
    if platform.system() != 'Windows':
        p =  subprocess.Popen('grep -Po \'^sudo.+:\K.*$\' /etc/group', stdout=subprocess.PIPE, shell = True)
        (output, err) = p.communicate()
        return output.decode('utf-8').strip()
    else:
        return "Windows Mock User"


def changeOwner(path):
    if platform.system() != 'Windows':
        exit_code = system((f'chown {getCurrentUser()} \"{path}\"'))
        return True if exit_code == 0 else False
    else:
        return True
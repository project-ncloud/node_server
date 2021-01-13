import subprocess
from os import system


def isAlive():
    return True if isProcessAlive("smbd") else False

def wake():
    ret = system("sudo systemctl start smbd")
    return True if ret == 0 else False


def kill():
    ret = system("sudo systemctl stop smbd")
    return True if ret == 0 else False


def isProcessAlive(processName:str):
    p =  subprocess.Popen(["systemctl", "is-active",  processName], stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    output:str = output.decode('utf-8')
    return True if output.strip().lower() == "active" else False


def getCurrentUser():
    p =  subprocess.Popen('grep -Po \'^sudo.+:\K.*$\' /etc/group', stdout=subprocess.PIPE, shell = True)
    (output, err) = p.communicate()
    return output.decode('utf-8').strip()
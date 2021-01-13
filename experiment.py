from samba.smb import SMB
from samba.smbhost import Host
sm = SMB('/etc/samba/smb.conf')
sm.forceUser("epicX")
print(sm.Hosts[0].config)
sm.pushIntoConf()


#os.system(f'sudo cat > /etc/samba/smb.conf << EOF\n{RAW}\nEOF')

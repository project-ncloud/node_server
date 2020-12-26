from main import SMB
from smbhost import Host

sm = SMB('./etc/samba/smb.conf')

sm.addValidUser('Vodai', 'ss')
sm.removeValidUser('Vodai', 'alfed')
sm.pushIntoConf()
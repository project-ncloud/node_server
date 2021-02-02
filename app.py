import dotenv
import os
import json

from flask          import Flask, jsonify, request
from samba.smb      import SMB
from serviceHandler import isAlive, wake, kill, getCurrentUser
from middleWare     import allowCors
from validation     import addressCorrect
from dotenv         import load_dotenv
from samba.utils          import isRequiredDataAvailable
from samba.smbhost  import Host

app = Flask(__name__)

app.SambaManager = SMB('/etc/samba/smb.conf')


#import routes.mainRoutes
#DB = db.Mongo(os.getenv('DB_URI_STRING'),os.getenv('DB_NAME'))


@app.route('/', methods = ['GET'])
def root():
    return "hello"


@app.route('/init/', methods = ['GET'])
def init():
    return allowCors(jsonify({}))


@app.route('/Pending/', methods = ['GET', 'POST'])
def pending():
    return allowCors(jsonify({}))


'''
Check if the server is alive or not
'''
@app.route('/alive/', methods = ['GET', 'POST'])
def alive():
    if request.method == 'GET':
        if isAlive():
            return allowCors(jsonify({"msg": "It is alive.","status": True}))
        else:
            return allowCors(jsonify({"msg": "It's dead.","status": False}))
    else:
        data = request.json
        if data.get('action') == True:
            if wake():
                return allowCors(jsonify({"msg": "Server started..","status": True}))
            else:
                return allowCors(jsonify({"msg": "Failed while starting","status": False}))
        elif data.get('action') == False:
            if kill():
                return allowCors(jsonify({"msg": "Server stopped","status": True}))
            else:
                return allowCors(jsonify({"msg": "Error Occured while killing service","status": False}))



'''
Add users to every host
Remove users from every host
'''
@app.route('/users/', methods = ['POST', 'DELETE'])
def usersOps():
    data = request.json

    if isRequiredDataAvailable(data, ["username", "password"]) == False:
        return allowCors(jsonify({"msg":"bad request"}), 400)

    username = data.get('username')
    password = data.get('password')

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    app.SambaManager.forceUser(getCurrentUser())

    operationCounter = 0

    for host in app.SambaManager.Hosts:
        if request.method == 'POST':
            if app.SambaManager.addValidUser(host.get('name'), username) == False:
                operationCounter += 1
        else:
            if app.SambaManager.removeValidUser(host.get('name'), username) == False:
                operationCounter += 1

    app.SambaManager.pushIntoConf()


    if request.method == 'POST':
        SMB.addUser(username)
        SMB.add_SMBUser(username, password)


    SMB.reloadSMBD()


    if operationCounter == 0:
        return allowCors(jsonify({"msg": f'{username} is added into all the host'}))
    
        
    return allowCors(jsonify({"msg": f'{username} is failed to while adding into {host.get("name")}'}), 400)
    





'''
Add user to specific host
Remove user from specific host
'''
@app.route('/user/', methods = ['POST', 'DELETE'])
def userOps():
    data = request.json

    if isRequiredDataAvailable(data, ["username", "password", "hostname"]) == False:
        return allowCors(jsonify({"msg":"bad request"}), 400)

    username = data.get('username')
    password = data.get('password')
    hostname = data.get('hostname')

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    app.SambaManager.forceUser(getCurrentUser())

    operationCounter = 0


    if request.method == 'POST':
        if app.SambaManager.addValidUser(hostname, username) == False:
            operationCounter += 1
    else:
        if app.SambaManager.removeValidUser(hostname, username) == False:
            operationCounter += 1
            
            

    app.SambaManager.pushIntoConf()


    if request.method == 'POST':
        SMB.addUser(username)
        SMB.add_SMBUser(username, password)



    SMB.reloadSMBD()

    if operationCounter == 0:
        return allowCors(jsonify({"msg": f'{username} is added into the host \t\t[{hostname}]'}))
    
    
    return allowCors(jsonify({"msg": f'{username} is failed to while adding into {hostname}'}), 401)



'''
Add host to the server
Remove host from the server
'''

@app.route('/host/', methods = ['POST', 'DELETE'])
def hostOps():
    if isRequiredDataAvailable(request.json, ["name", "path"]) == False:
        return allowCors(jsonify({"msg":"bad request"}), 400)

    req = request.json

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    operationCounter = 0


    if request.method == 'POST':
        if isRequiredDataAvailable(request.json, ["name", "path", "writable", "public"]) == False:
            return allowCors(jsonify({"msg":"bad request"}), 400)

        if app.SambaManager.createNewHost(Host(data = {
            "name" : req.get('name'),
            "path" : req.get('path'),
            "writable" : ("Yes" if req.get('writable') == True else "No"),
            "create mask" : '0777',
            "directory mask" : '0777',
            "public" : "Yes" if req.get('public') == True else "No",
            "valid users" : [] 
        })) == False:
            operationCounter += 1  
    else:
        if app.SambaManager.removeHost(req.get('name'), True if req.get('removeAll') == True else False) == False:
            operationCounter += 1
            
            
    app.SambaManager.forceUser(getCurrentUser())

    app.SambaManager.pushIntoConf()

    SMB.reloadSMBD()


    if operationCounter == 0:
        return allowCors(jsonify({"msg": f'{req.get("name")} is {"added into" if request.method == "POST" else "removed from"} the server'}))
    
    
    return allowCors(jsonify({"msg": f'{req.get("name")} is failed while {"adding into" if request.method == "POST" else "removing from"} the server'}))



'''
{
	"name" : "NAS2",                            //Update    hostname        [Only when update]
	"currentHostName" : "NAS2",                 //Current   hostname        [REQUIRED]
	"path" : "/home/epicx/Desktop/Drive2",      //Update    path            [Only when update]
	"writable" : true,                          //Update    writable        [Only when update]
	"public" : false,                           //Update    guestAccess     [Only when update]
	"wipeData" : true                           //Optional  wipe prev path entirely if new path updated
}

1. wipedata only works if new paths updated. Its totally optional flag.
2. If we are not gonna change some props then send existing data

Note - This route is not for adding valid users into the hosts/host use /host/ or /hosts/ instead
'''
@app.route('/host/config/', methods = ['POST'])
def hostConfigOps():
    if isRequiredDataAvailable(request.json, ["currentHostName"]) == False:
        return allowCors(jsonify({"msg":"bad request"}), 400)

    req = request.json

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    uPublic = None
    if req.get('public') != None:
        uPublic = "Yes" if req.get('public') == True else "No"

    uWritable = None
    if req.get('writable') != None:
        uWritable = "Yes" if req.get('writable') == True else "No"

    ret = app.SambaManager.updateHost(name=req.get('name'), path=req.get('path'), writable = uWritable, public = uPublic, hostname = req.get('currentHostName'), wipeData = req.get('wipeData'))


    if ret == False:
        return allowCors(jsonify({"msg":"Requested Host not found."}), 404)

    
            
            
    app.SambaManager.forceUser(getCurrentUser())

    app.SambaManager.pushIntoConf()

    SMB.reloadSMBD()



    return allowCors(jsonify({"msg": f'Successfully updated the host'}))













#sudo systemctl daemon-reload






















    
if __name__ == '__main__':
    #sm = SMB('./etc/samba/smb.conf')
    load_dotenv('.env')
    SMB.addUser(os.getenv('ADMIN_USER'))
    SMB.add_SMBUser(os.getenv('ADMIN_USER'), os.getenv('ADMIN_KEY'))

    
    app.run(host = '0.0.0.0', port = 6900, debug = True)

    

import dotenv
import os
import json
import pathlib
import platform
import logging

from flask                  import Flask, jsonify, request, send_file, send_from_directory, safe_join, abort
from flask_cors             import CORS, cross_origin
from samba.smb              import SMB
from serviceHandler         import isAlive, wake, kill, getCurrentUser, changeOwner
from middleWare             import allowCors
from validation             import addressCorrect, isValidPath
from dotenv                 import load_dotenv
from samba.utils            import isRequiredDataAvailable
from samba.smbhost          import Host
from os                     import getenv, path
from pathlib                import Path

from Directories   import Directories

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token
)


app = Flask(__name__)

CORS(app)
app.config['JWT_SECRET_KEY'] = getenv('SECRET_KEY')
jwt = JWTManager(app)

app.SambaManager = SMB("/etc/samba/smb.conf")

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

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


    is_required_data_available = isRequiredDataAvailable(data, ["username", "password", "hostname"]) if request.method == 'POST' else isRequiredDataAvailable(data, ["username", "hostname"]) 

    if is_required_data_available == False:
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



@app.route('/reset/', methods = ['GET'])
def resetServer():
    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    for host in app.SambaManager.Hosts:
        app.SambaManager.removeHost(host.get('name'))


    app.SambaManager.pushIntoConf()

    SMB.restartSMBD()

    return allowCors(jsonify({"msg": "Sucessful"}))






#From TempServer

@app.route('/file/upload/', methods = ['GET', 'POST'])
@jwt_required
def uploadFile():
    files = request.files
    req = request.args

    token = req.get("token")
    tokenData = decode_token(token)

    tokenIdentity = tokenData.get("identity")
    payload = tokenData.get("user_claims")

    if tokenIdentity.get("username") != get_jwt_identity():
        return allowCors(jsonify({"msg" : "Corrupted user"}), 400)

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    host = app.SambaManager.getHost(payload.get("host_name"))

    if host == None:
        return allowCors(jsonify({"msg":"Token Host is not same as requested host."}))

    if host.get("writable") == False:
        return allowCors(jsonify({"msg":"You dont have write permission."}))


    if isValidPath(req, host.get("path")):
        files['file'].save(path.join(req.get('path'), files['file'].filename))
        changeOwner(path.join(req.get('path'), files['file'].filename))
        return allowCors(jsonify({"msg":"Success"}))
    else:
        return allowCors(jsonify({"msg": "Invalid Path"}), 400)


@app.route("/testRoute/", methods = ["GET", "POST"])
def heelo():
    req = request.args

    mainToken = decode_token(req.get("m_token"))
    token = req.get("token")

    tokenData = decode_token(token)

    tokenIdentity = tokenData.get("identity")

    if tokenIdentity.get("username") != mainToken.get("identity"):
        return allowCors(jsonify({"msg" : "Corrupted user"}), 400)


    payload = tokenData.get("user_claims")

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    host = app.SambaManager.getHost(payload.get("host_name"))

    if host == None:
        return allowCors(jsonify({"msg":"Token Host is not same as requested host."}))


    if isValidPath({"path": safe_join(req.get('path'), req.get('file_name'))}, host.get("path"), False):
        return send_from_directory(Path(req.get('path')), filename = req.get('file_name'), as_attachment=True)
    else:
        return allowCors(jsonify({"msg" : "Invalid Path"}), 400)


@app.route("/dir/", methods = ['GET'])
@jwt_required
def getFolder():
    req = request.args

    token = req.get("token")
    tokenData = decode_token(token)

    tokenIdentity = tokenData.get("identity")

    if tokenIdentity.get("username") != get_jwt_identity():
        return allowCors(jsonify({"msg" : "Corrupted user"}), 400)

    path = req.get('path')

    if path:
        path = path.strip()

    if path == None or path == '':
        return allowCors(jsonify({"path":None, "data":[]}))

    if not Path(path).exists():
        return allowCors(jsonify({"path":None, "data":[]}))

    data = Directories.getDirData(req.get('path'))

    return allowCors(jsonify(data))



@app.route("/dir/create/", methods = ["POST"])
@jwt_required
def createFolder():
    req = request.json

    token = req.get("token")

    tokenData = decode_token(token)

    tokenIdentity = tokenData.get("identity")

    if tokenIdentity.get("username") != get_jwt_identity():
        return allowCors(jsonify({"msg" : "Corrupted user"}), 400)


    payload = tokenData.get("user_claims")

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    host = app.SambaManager.getHost(payload.get("host_name"))

    if host == None:
        return allowCors(jsonify({"msg":"Token Host is not same as requested host."}), 400)

    if host.get("writable") == False and not payload.get("writable"):
        return allowCors(jsonify({"msg":"You dont have write permission."}), 400)

    if isValidPath({"path": req.get('path')}, host.get("path")):
        fullPath = safe_join(req.get('path'), req.get('folder_name'))
        exit_code = os.system(f'mkdir -p \"{fullPath}\"') if platform.system() != 'Windows' else os.system(f'mkdir \"{fullPath}\"')

        if exit_code == 0 and changeOwner(fullPath):
            return allowCors(jsonify({"msg":"Folder Created"}))
        else:
            return allowCors(jsonify({"msg" : f'Error ocurred with exit {exit_code}'}), 400)
    else:
        return allowCors(jsonify({"msg":"Invalid Path"}), 400)



@app.route("/dir/remove/", methods = ["DELETE"])
@jwt_required
def removeDir():
    req = request.json

    token = req.get("token")

    tokenData = decode_token(token)

    tokenIdentity = tokenData.get("identity")

    if tokenIdentity.get("username") != get_jwt_identity():
        return allowCors(jsonify({"msg" : "Corrupted user"}), 400)


    payload = tokenData.get("user_claims")

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    host = app.SambaManager.getHost(payload.get("host_name"))

    if host == None:
        return allowCors(jsonify({"msg":"Token Host is not same as requested host."}), 400)

    if host.get("writable") == False and not payload.get("writable"):
        return allowCors(jsonify({"msg":"You dont have write permission."}), 400)

    if isValidPath({"path": req.get('path')}, host.get("path")):
        fullPath = safe_join(req.get('path'), req.get('folder_name'))
        exit_code = os.system(f'rmdir /s \"{fullPath}\"') if platform.system() != 'Windows' else os.system(f'rm -rf \"{fullPath}\"')

        if exit_code == 0 and changeOwner(fullPath):
            return allowCors(jsonify({"msg":"Folder Removed"}))
        else:
            return allowCors(jsonify({"msg" : f'Error ocurred with exit {exit_code}'}), 400)
    else:
        return allowCors(jsonify({"msg":"Invalid Path"}), 400)


@app.route("/file/remove/", methods = ["DELETE"])
@jwt_required
def removeFile():
    req = request.json

    token = req.get("token")

    tokenData = decode_token(token)

    tokenIdentity = tokenData.get("identity")

    if tokenIdentity.get("username") != get_jwt_identity():
        return allowCors(jsonify({"msg" : "Corrupted user"}), 400)


    payload = tokenData.get("user_claims")

    #LOAD ALL CONFIGS from smb.conf
    app.SambaManager.loadConfigs()

    host = app.SambaManager.getHost(payload.get("host_name"))

    if host == None:
        return allowCors(jsonify({"msg":"Token Host is not same as requested host."}), 400)

    if host.get("writable") == False and not payload.get("writable"):
        return allowCors(jsonify({"msg":"You dont have write permission."}), 400)

    if isValidPath({"path": req.get('path')}, host.get("path")):
        fullPath = safe_join(req.get('path'), req.get('file_name'))
        exit_code = os.system(f'del /f \"{fullPath}\"') if platform.system() != 'Windows' else os.system(f'rm -rf \"{fullPath}\"')

        if exit_code == 0 and changeOwner(fullPath):
            return allowCors(jsonify({"msg":"File Removed"}))
        else:
            return allowCors(jsonify({"msg" : f'Error ocurred with exit {exit_code}'}), 400)
    else:
        return allowCors(jsonify({"msg":"Invalid Path"}), 400)






















    
if __name__ == '__main__':
    #sm = SMB('./etc/samba/smb.conf')
    load_dotenv('.env')
    SMB.addUser(os.getenv('ADMIN_USER'))
    SMB.add_SMBUser(os.getenv('ADMIN_USER'), os.getenv('ADMIN_KEY'))

    
    app.run(host = '0.0.0.0', port = 6900, debug = True)

    

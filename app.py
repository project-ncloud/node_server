import dotenv
import os
import json

from flask          import Flask, jsonify, request
from samba.smb      import SMB
from serviceHandler import isAlive, wake, kill
from middleWare     import allowCors

app = Flask(__name__)


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



@app.route('/alive/', methods = ['GET', 'POST'])
def alive():
    if request.method == 'GET':
        if isAlive():
            return allowCors(jsonify({"msg": "It is alive.","status": True}))
        else:
            return allowCors(jsonify({"msg": "It's dead.","status": False}))
    else:
        data:dict = request.json
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

if __name__ == '__main__':
    #sm = SMB('./etc/samba/smb.conf')
    app.run('localhost', 3000, True)

    

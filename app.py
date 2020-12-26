from samba.smb import SMB
import dotenv
import os
import json

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)


#DB = db.Mongo(os.getenv('DB_URI_STRING'),os.getenv('DB_NAME'))


@app.route('/', methods = ['GET'])
def root():
    return "hello"



if __name__ == '__main__':
    sm = SMB('./etc/samba/smb.conf')
    app.run(debug = True , port = 6900)

    

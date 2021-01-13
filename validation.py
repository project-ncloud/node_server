import subprocess
from functools import wraps
from middleWare import allowCors
from flask import request, jsonify


def addressCorrect(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        data = request.json
        if data == None or data.get('address') == None:
            return allowCors(jsonify({"msg":"bad request"}), 400)
        else:
            address = data.get('address')

        output, err = subprocess.Popen(['hostname', '-i'], stdout=subprocess.PIPE).communicate()
        ip = output.decode().strip()

        return func(*args, **kwargs) if ip in address else allowCors(jsonify({"msg":"bad request"}), 400)
    return decorator

#print(addressCorrect('127.0.1.1:5000'))



def testOne(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if 1 == 2:
            return func(*args, **kwargs)
        else:
            return "fuk"

    return decorator



def testtwo(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if 1 == 1:
            return func(*args, **kwargs)
        else:
            return "hello"

    return decorator


    
@testtwo
def f():
    return 'world'





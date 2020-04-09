from uuid import uuid4
from base64 import b64encode

def generate_token():
    token = uuid4().hex
    print('Token:\t\t', token)
    t = '%s:' % token
    b64 = b64encode(t.encode('utf-8'))
    client_token = b64.decode('utf-8')
    print('Client Token:\t', client_token)
    return True, token, client_token

if __name__ == '__main__':
    generate_token()

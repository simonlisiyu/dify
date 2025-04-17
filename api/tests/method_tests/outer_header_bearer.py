# __author__ "lisiyu"
# date 2024/11/30

import jwt

# Define the client tokens dictionary
client_tokens = {"haizhi": "haizhi", "client2": "zzz"}
client_secret = "haizhi_secret"

client_id = "haizhi"
token = jwt.encode({'client_id': client_id}, client_secret, algorithm='HS256')
headers = {'Authorization': 'Bearer ' + token}
print(headers)


token_type, token = headers["Authorization"].split(None, 1)
if token_type.lower() == 'bearer':
    print(f"token={token}")
    try:
        decoded_token = jwt.decode(token, client_secret, algorithms=['HS256'])
        if 'client_id' in decoded_token:
            client_id = decoded_token['client_id']
            print(f"token={client_tokens[client_id]}")
            if client_id in client_tokens:
                print(f"token={token} success")
            else:
                print(f"client_id={client_id} failed")
        else:
            print("client_id is not exist.")
    except jwt.InvalidTokenError:
        print("jwt.decode failed.")
else:
    print("token type is not Bearer.")

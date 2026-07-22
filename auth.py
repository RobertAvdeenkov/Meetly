from jose import jwt
import jose.exceptions
from config import SECRET,ALGORITHM
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends

oauth=OAuth2PasswordBearer(tokenUrl='reglog')

def create_token(usersname:str):
    payload={
        'sub':usersname,
        'exp':datetime.now()+timedelta(hours=1)
    }
    token=jwt.encode(payload, SECRET,ALGORITHM)
    return token

def get_user(token:str=Depends(oauth)):
    try:
        data=jwt.decode(token,SECRET,algorithms=[ALGORITHM])
        return data['sub']
    except Exception as e:
        print('Error:',e)
        
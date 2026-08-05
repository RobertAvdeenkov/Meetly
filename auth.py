from jose import jwt
from jose.exceptions import JWTError,ExpiredSignatureError
from config import SECRET,ALGORITHM
from datetime import datetime,timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends,HTTPException

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

def get_by_token(token:str):
    try:
        data=jwt.decode(token,SECRET, algorithms=[ALGORITHM])
        return data['sub']
    except ExpiredSignatureError:
            raise HTTPException(401, 'Токен протух!')
    except JWTError:
        raise HTTPException(401, 'Неверный токен')
        
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

#TODO later
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from boto3 import client
import os

def get_secret_key():
    # Try environment variable first (local development)
    secret_key = os.getenv("JWT_SECRET_KEY")
    if secret_key:
        return secret_key
    
    # Try AWS Parameter Store (Lambda/production)
    try:
        ssm = client('ssm')
        response = ssm.get_parameter(Name='/f1tof12/jwt-secret', WithDecryption=True)
        return response['Parameter']['Value']
    except Exception:
        raise ValueError("JWT_SECRET_KEY not found in environment or Parameter Store")

SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 45

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

security = HTTPBearer()

def verify_cognito_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    cognito_client = client('cognito-idp', region_name='us-east-1')
    try:
        response = cognito_client.get_user(AccessToken=credentials.credentials)
        return response['Username']
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cognito token")
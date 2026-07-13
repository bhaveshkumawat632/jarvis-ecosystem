from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import datetime

# --- Enterprise Platform Security Layer ---
# This transitions the system from a CLI app to a secure cloud service capable 
# of managing user seats, enterprise licenses, and authenticated quotas.

SECRET_KEY = "super_secure_enterprise_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserData(BaseModel):
    username: str
    role: str
    license_tier: str

def create_access_token(data: dict):
    """Generates an Enterprise JWT"""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserData:
    """
    Validates the JWT on protected endpoints to ensure only licensed 
    enterprise users can trigger expensive API renders.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        role: str = payload.get("role", "user")
        tier: str = payload.get("tier", "basic")
    except jwt.PyJWTError:
        raise credentials_exception
        
    return UserData(username=username, role=role, license_tier=tier)

def verify_enterprise_license(user: UserData = Depends(get_current_user)):
    """Role-based access control ensuring enterprise-only features are locked."""
    if user.license_tier != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operation requires an active Enterprise License."
        )
    return user

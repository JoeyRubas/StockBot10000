from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import os
import json

router = APIRouter()
security = HTTPBearer()

# Initialize Firebase only once
if not firebase_admin._apps:
    firebase_creds_env = os.getenv("FIREBASE_CREDENTIALS")

    if firebase_creds_env:
        # On Heroku: credentials from env variable (as JSON string)
        firebase_creds = json.loads(firebase_creds_env)
        cred = credentials.Certificate(firebase_creds)
    else:
        # Local dev: use file-based credentials
        cred = credentials.Certificate("firebase-credentials.json")

    firebase_admin.initialize_app(cred)

# Middleware to verify token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        decoded_token = firebase_auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

# Test endpoint
@router.get("/verify")
def verify_user(user_data=Depends(verify_token)):
    return {"uid": user_data["uid"], "email": user_data.get("email")}
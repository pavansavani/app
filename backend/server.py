from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from cryptography.fernet import Fernet
import base64
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Encryption setup
encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

# Security
security = HTTPBearer(auto_error=False)

# Define Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: str
    app_lock_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WebsiteEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    link: str
    purpose: str
    login_id: Optional[str] = None
    password: Optional[str] = None  # This will be encrypted
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AppEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    app_name: str
    purpose: str
    username: Optional[str] = None
    password: Optional[str] = None  # This will be encrypted
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OtherNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request Models
class WebsiteEntryCreate(BaseModel):
    name: str
    link: str
    purpose: str
    login_id: Optional[str] = None
    password: Optional[str] = None

class AppEntryCreate(BaseModel):
    app_name: str
    purpose: str
    username: Optional[str] = None
    password: Optional[str] = None

class OtherNoteCreate(BaseModel):
    title: str
    content: str

class SetAppLockRequest(BaseModel):
    password: str

class VerifyAppLockRequest(BaseModel):
    password: str

class SessionRequest(BaseModel):
    session_id: str

# Helper functions
def encrypt_data(data: str) -> str:
    if not data:
        return data
    return base64.b64encode(cipher_suite.encrypt(data.encode())).decode()

def decrypt_data(encrypted_data: str) -> str:
    if not encrypted_data:
        return encrypted_data
    try:
        return cipher_suite.decrypt(base64.b64decode(encrypted_data.encode())).decode()
    except:
        return encrypted_data  # Return as-is if decryption fails

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

async def get_current_user(request: Request) -> Optional[User]:
    # First check cookies for session_token
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            session_token = authorization.split(" ")[1]
    
    if not session_token:
        return None
    
    # Find session in database
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session or datetime.now(timezone.utc) > session["expires_at"]:
        return None
    
    # Find user
    user = await db.users.find_one({"id": session["user_id"]})
    if not user:
        return None
    
    return User(**user)

# Authentication endpoints
@api_router.post("/auth/session")
async def process_session(request: SessionRequest, response: Response):
    """Process session_id from Emergent Auth"""
    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id}
            )
            if auth_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid session ID")
            
            auth_data = auth_response.json()
            
            # Check if user exists
            existing_user = await db.users.find_one({"email": auth_data["email"]})
            if not existing_user:
                # Create new user
                user = User(
                    email=auth_data["email"],
                    name=auth_data["name"],
                    picture=auth_data["picture"]
                )
                await db.users.insert_one(user.dict())
            else:
                user = User(**existing_user)
            
            # Create session
            session = UserSession(
                user_id=user.id,
                session_token=auth_data["session_token"],
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            await db.user_sessions.insert_one(session.dict())
            
            # Set cookie
            response.set_cookie(
                key="session_token",
                value=auth_data["session_token"],
                max_age=7 * 24 * 60 * 60,  # 7 days
                httponly=True,
                secure=True,
                samesite="none",
                path="/"
            )
            
            return {"user": user, "needs_app_lock": user.app_lock_hash is not None}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    user = await get_current_user(request)
    if user:
        session_token = request.cookies.get("session_token")
        if session_token:
            await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_current_user_info(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user, "needs_app_lock": user.app_lock_hash is not None}

# App Lock endpoints
@api_router.post("/auth/set-app-lock")
async def set_app_lock(request: Request, app_lock_request: SetAppLockRequest):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    hashed_password = hash_password(app_lock_request.password)
    await db.users.update_one(
        {"id": user.id},
        {"$set": {"app_lock_hash": hashed_password}}
    )
    return {"message": "App lock set successfully"}

@api_router.post("/auth/verify-app-lock")
async def verify_app_lock(request: Request, verify_request: VerifyAppLockRequest):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not user.app_lock_hash:
        raise HTTPException(status_code=400, detail="No app lock set")
    
    if not verify_password(verify_request.password, user.app_lock_hash):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    return {"message": "App lock verified"}

@api_router.delete("/auth/remove-app-lock")
async def remove_app_lock(request: Request, verify_request: VerifyAppLockRequest):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not user.app_lock_hash:
        raise HTTPException(status_code=400, detail="No app lock set")
    
    if not verify_password(verify_request.password, user.app_lock_hash):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    await db.users.update_one(
        {"id": user.id},
        {"$unset": {"app_lock_hash": ""}}
    )
    return {"message": "App lock removed"}

# Website entries endpoints
@api_router.post("/websites", response_model=WebsiteEntry)
async def create_website_entry(request: Request, entry: WebsiteEntryCreate):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    entry_dict = entry.dict()
    entry_dict["user_id"] = user.id
    
    # Encrypt password if provided
    if entry_dict.get("password"):
        entry_dict["password"] = encrypt_data(entry_dict["password"])
    
    website_entry = WebsiteEntry(**entry_dict)
    await db.website_entries.insert_one(website_entry.dict())
    
    # Decrypt password for response
    if website_entry.password:
        website_entry.password = decrypt_data(website_entry.password)
    
    return website_entry

@api_router.get("/websites", response_model=List[WebsiteEntry])
async def get_website_entries(request: Request, search: Optional[str] = None):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"user_id": user.id}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"link": {"$regex": search, "$options": "i"}},
            {"purpose": {"$regex": search, "$options": "i"}}
        ]
    
    entries = await db.website_entries.find(query).sort("created_at", -1).to_list(1000)
    
    # Decrypt passwords
    for entry in entries:
        if entry.get("password"):
            entry["password"] = decrypt_data(entry["password"])
    
    return [WebsiteEntry(**entry) for entry in entries]

@api_router.put("/websites/{entry_id}", response_model=WebsiteEntry)
async def update_website_entry(request: Request, entry_id: str, entry_update: WebsiteEntryCreate):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    entry_dict = entry_update.dict()
    entry_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Encrypt password if provided
    if entry_dict.get("password"):
        entry_dict["password"] = encrypt_data(entry_dict["password"])
    
    result = await db.website_entries.update_one(
        {"id": entry_id, "user_id": user.id},
        {"$set": entry_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Website entry not found")
    
    updated_entry = await db.website_entries.find_one({"id": entry_id, "user_id": user.id})
    
    # Decrypt password for response
    if updated_entry.get("password"):
        updated_entry["password"] = decrypt_data(updated_entry["password"])
    
    return WebsiteEntry(**updated_entry)

@api_router.delete("/websites/{entry_id}")
async def delete_website_entry(request: Request, entry_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.website_entries.delete_one({"id": entry_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Website entry not found")
    
    return {"message": "Website entry deleted successfully"}

# App entries endpoints
@api_router.post("/apps", response_model=AppEntry)
async def create_app_entry(request: Request, entry: AppEntryCreate):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    entry_dict = entry.dict()
    entry_dict["user_id"] = user.id
    
    # Encrypt password if provided
    if entry_dict.get("password"):
        entry_dict["password"] = encrypt_data(entry_dict["password"])
    
    app_entry = AppEntry(**entry_dict)
    await db.app_entries.insert_one(app_entry.dict())
    
    # Decrypt password for response
    if app_entry.password:
        app_entry.password = decrypt_data(app_entry.password)
    
    return app_entry

@api_router.get("/apps", response_model=List[AppEntry])
async def get_app_entries(request: Request, search: Optional[str] = None):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"user_id": user.id}
    if search:
        query["$or"] = [
            {"app_name": {"$regex": search, "$options": "i"}},
            {"purpose": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}}
        ]
    
    entries = await db.app_entries.find(query).sort("created_at", -1).to_list(1000)
    
    # Decrypt passwords
    for entry in entries:
        if entry.get("password"):
            entry["password"] = decrypt_data(entry["password"])
    
    return [AppEntry(**entry) for entry in entries]

@api_router.put("/apps/{entry_id}", response_model=AppEntry)
async def update_app_entry(request: Request, entry_id: str, entry_update: AppEntryCreate):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    entry_dict = entry_update.dict()
    entry_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Encrypt password if provided
    if entry_dict.get("password"):
        entry_dict["password"] = encrypt_data(entry_dict["password"])
    
    result = await db.app_entries.update_one(
        {"id": entry_id, "user_id": user.id},
        {"$set": entry_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="App entry not found")
    
    updated_entry = await db.app_entries.find_one({"id": entry_id, "user_id": user.id})
    
    # Decrypt password for response
    if updated_entry.get("password"):
        updated_entry["password"] = decrypt_data(updated_entry["password"])
    
    return AppEntry(**updated_entry)

@api_router.delete("/apps/{entry_id}")
async def delete_app_entry(request: Request, entry_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.app_entries.delete_one({"id": entry_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="App entry not found")
    
    return {"message": "App entry deleted successfully"}

# Other notes endpoints
@api_router.post("/notes", response_model=OtherNote)
async def create_note(request: Request, note: OtherNoteCreate):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    note_dict = note.dict()
    note_dict["user_id"] = user.id
    
    other_note = OtherNote(**note_dict)
    await db.other_notes.insert_one(other_note.dict())
    return other_note

@api_router.get("/notes", response_model=List[OtherNote])
async def get_notes(request: Request, search: Optional[str] = None):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {"user_id": user.id}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    
    notes = await db.other_notes.find(query).sort("created_at", -1).to_list(1000)
    return [OtherNote(**note) for note in notes]

@api_router.put("/notes/{note_id}", response_model=OtherNote)
async def update_note(request: Request, note_id: str, note_update: OtherNoteCreate):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    note_dict = note_update.dict()
    note_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.other_notes.update_one(
        {"id": note_id, "user_id": user.id},
        {"$set": note_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    
    updated_note = await db.other_notes.find_one({"id": note_id, "user_id": user.id})
    return OtherNote(**updated_note)

@api_router.delete("/notes/{note_id}")
async def delete_note(request: Request, note_id: str):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = await db.other_notes.delete_one({"id": note_id, "user_id": user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"message": "Note deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
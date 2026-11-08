"""
Pax Modernica - Auth Router
Endpoints for user registration, authentication and session verification.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from server.database.connection import get_db
from server.auth.security import hash_password, verify_password, generate_session_token, calculate_expiry
from server.simulation.engine import engine
from server.websocket.connection_manager import manager
from datetime import datetime, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)

class LoginRequest(BaseModel):
    username: str
    password: str

class ClaimNationRequest(BaseModel):
    nation_id: str

class UserResponse(BaseModel):
    id: str
    username: str
    is_admin: bool
    assigned_nation_id: Optional[str] = None
    token: Optional[str] = None

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Dependency to extract authenticated user from Authorization header (Bearer <token>)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    
    async with get_db() as db:
        async with db.execute(
            """
            SELECT a.id, a.username, a.is_admin, a.assigned_nation_id, s.expires_at 
            FROM sessions s
            JOIN accounts a ON s.account_id = a.id
            WHERE s.token = ?
            """,
            (token,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            # Check expiry
            expires_at = datetime.fromisoformat(row["expires_at"]) if isinstance(row["expires_at"], str) else row["expires_at"]
            if expires_at < datetime.now(timezone.utc):
                await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
                await db.commit()
                return None
            
            return {
                "id": row["id"],
                "username": row["username"],
                "is_admin": bool(row["is_admin"]),
                "assigned_nation_id": row["assigned_nation_id"],
                "token": token
            }

@router.post("/register", response_model=UserResponse)
async def register(req: RegisterRequest):
    username = req.username.strip()
    if not username.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Benutzername darf nur Buchstaben, Zahlen und Unterstriche enthalten.")

    async with get_db() as db:
        # Check if username exists (case-insensitive)
        async with db.execute("SELECT id FROM accounts WHERE username = ? COLLATE NOCASE", (username,)) as cur:
            if await cur.fetchone():
                raise HTTPException(status_code=409, detail="Benutzername ist bereits vergeben. Bitte wähle einen anderen Namen.")
        
        # Check if this is the first user (becomes Admin/Host)
        async with db.execute("SELECT COUNT(*) as cnt FROM accounts") as cur:
            row = await cur.fetchone()
            is_admin = 1 if row["cnt"] == 0 else 0
        
        user_id = str(uuid.uuid4())
        hashed = hash_password(req.password)
        
        await db.execute(
            "INSERT INTO accounts (id, username, password_hash, is_admin, assigned_nation_id) VALUES (?, ?, ?, ?, NULL)",
            (user_id, username, hashed, is_admin)
        )
        
        # Create initial session
        token = generate_session_token()
        expiry = calculate_expiry().isoformat()
        await db.execute(
            "INSERT INTO sessions (token, account_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expiry)
        )
        await db.commit()

        return UserResponse(
            id=user_id,
            username=username,
            is_admin=bool(is_admin),
            assigned_nation_id=None,
            token=token
        )

@router.post("/login", response_model=UserResponse)
async def login(req: LoginRequest):
    async with get_db() as db:
        async with db.execute(
            "SELECT id, username, password_hash, is_admin, assigned_nation_id FROM accounts WHERE username = ? COLLATE NOCASE",
            (req.username.strip(),)
        ) as cur:
            user = await cur.fetchone()
            if not user or not verify_password(req.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Ungültiger Benutzername oder falsches Passwort.")
            
            token = generate_session_token()
            expiry = calculate_expiry().isoformat()
            await db.execute(
                "INSERT INTO sessions (token, account_id, expires_at) VALUES (?, ?, ?)",
                (token, user["id"], expiry)
            )
            await db.execute("UPDATE accounts SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
            await db.commit()

            return UserResponse(
                id=user["id"],
                username=user["username"],
                is_admin=bool(user["is_admin"]),
                assigned_nation_id=user["assigned_nation_id"],
                token=token
            )

@router.get("/me", response_model=UserResponse)
async def me(current_user: Optional[dict] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert.")
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        is_admin=current_user["is_admin"],
        assigned_nation_id=current_user.get("assigned_nation_id"),
        token=current_user["token"]
    )

@router.get("/claimed-nations")
async def get_claimed_nations():
    """Returns currently occupied nations and which player governs them."""
    return {
        "claimed_nations": getattr(engine.world, "claimed_nations", {})
    }

@router.post("/claim-nation", response_model=UserResponse)
async def claim_nation(req: ClaimNationRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """Locks a nation to an account so only one player can control each nation."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Bitte melde dich an, um eine Nation zu wählen.")
    
    target_nid = req.nation_id
    if target_nid not in engine.world.nations:
        raise HTTPException(status_code=404, detail="Nation nicht gefunden.")

    async with get_db() as db:
        # Check if nation is already claimed by someone else
        async with db.execute(
            "SELECT id, username FROM accounts WHERE assigned_nation_id = ? AND id != ?",
            (target_nid, current_user["id"])
        ) as cur:
            other = await cur.fetchone()
            if other:
                raise HTTPException(
                    status_code=409,
                    detail=f"Diese Nation ist bereits durch den Herrscher '{other['username']}' besetzt!"
                )
        
        # Free up any previously claimed nation by this user in memory
        old_nid = current_user.get("assigned_nation_id")
        if old_nid and old_nid in engine.world.claimed_nations:
            del engine.world.claimed_nations[old_nid]

        # Update DB
        await db.execute(
            "UPDATE accounts SET assigned_nation_id = ? WHERE id = ?",
            (target_nid, current_user["id"])
        )
        await db.commit()

        # Update in-memory world state
        engine.world.claimed_nations[target_nid] = {
            "account_id": current_user["id"],
            "username": current_user["username"]
        }
        engine.world.active_players[current_user["id"]] = target_nid

        # Broadcast claim to all connected players in real-time
        await manager.broadcast({
            "type": "NATION_CLAIMED",
            "nation_id": target_nid,
            "account_id": current_user["id"],
            "username": current_user["username"],
            "claimed_nations": engine.world.claimed_nations
        })

        return UserResponse(
            id=current_user["id"],
            username=current_user["username"],
            is_admin=current_user["is_admin"],
            assigned_nation_id=target_nid,
            token=current_user["token"]
        )

@router.post("/logout")
async def logout(current_user: Optional[dict] = Depends(get_current_user)):
    if current_user and current_user.get("token"):
        async with get_db() as db:
            await db.execute("DELETE FROM sessions WHERE token = ?", (current_user["token"],))
            await db.commit()
    return {"status": "ok"}

"""
Unit tests for Pax Modernica Argon2id Security & Auth.
"""

import pytest
from server.auth.security import hash_password, verify_password, generate_session_token

def test_argon2id_hashing():
    pw = "Kaiserreich1700!"
    hashed = hash_password(pw)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_session_token_entropy():
    t1 = generate_session_token()
    t2 = generate_session_token()
    assert len(t1) == 64
    assert t1 != t2

@pytest.mark.asyncio
async def test_duplicate_username_and_claim_nation():
    from server.auth.router import register, claim_nation, RegisterRequest, ClaimNationRequest
    from server.database.connection import init_db
    from fastapi import HTTPException
    from server.simulation.engine import engine

    await init_db()
    # Initialize engine world nations if not already loaded
    if not engine.world.nations:
        engine.world.load_state_from_data()

    import uuid
    suffix = uuid.uuid4().hex[:6]
    name1 = f"TestKaiser_{suffix}"

    # 1. Register first user
    u1_req = RegisterRequest(username=name1, password="password123")
    res1 = await register(u1_req)
    assert res1.username == name1
    assert res1.assigned_nation_id is None

    # 2. Register duplicate with different casing -> must raise 409
    dup_req = RegisterRequest(username=name1.lower(), password="password456")
    with pytest.raises(HTTPException) as exc_info:
        await register(dup_req)
    assert exc_info.value.status_code == 409
    assert "bereits vergeben" in exc_info.value.detail

    from server.database.connection import get_db

    target_nid = "nation_bavaria"
    async with get_db() as db:
        await db.execute("UPDATE accounts SET assigned_nation_id = NULL WHERE assigned_nation_id = ?", (target_nid,))
        await db.commit()
    if target_nid in engine.world.claimed_nations:
        del engine.world.claimed_nations[target_nid]

    # 3. User 1 claims target_nid
    current_u1 = {"id": res1.id, "username": res1.username, "is_admin": res1.is_admin, "token": res1.token}
    claim_req1 = ClaimNationRequest(nation_id=target_nid)
    claimed_res1 = await claim_nation(claim_req1, current_user=current_u1)
    assert claimed_res1.assigned_nation_id == target_nid
    assert engine.world.claimed_nations[target_nid]["account_id"] == res1.id

    # 4. Register second user
    u2_req = RegisterRequest(username=f"TestKaiser2_{suffix}", password="password789")
    res2 = await register(u2_req)
    current_u2 = {"id": res2.id, "username": res2.username, "is_admin": res2.is_admin, "token": res2.token}

    # 5. User 2 tries to claim the already occupied target_nid -> must raise 409
    claim_req2 = ClaimNationRequest(nation_id=target_nid)
    with pytest.raises(HTTPException) as exc_info2:
        await claim_nation(claim_req2, current_user=current_u2)
    assert exc_info2.value.status_code == 409
    assert "besetzt" in exc_info2.value.detail

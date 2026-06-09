"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Form, Depends
from app.core.authenticate import Authenticator

router = APIRouter()


@router.post("/login")
async def login(
    face_image: UploadFile = File(...),
    device_id: str = Form(...),
    platform: str = Form("web"),
):
    image_bytes = await face_image.read()
    authenticator = Authenticator()
    result = await authenticator.authenticate(image_bytes, device_id, platform)
    return result


@router.post("/continuous-verify")
async def continuous_verify(
    face_image: UploadFile = File(...),
    session_token: str = Form(...),
):
    from app.core.token_service import TokenService
    ts = TokenService()
    payload = ts.validate(session_token)

    image_bytes = await face_image.read()
    authenticator = Authenticator()
    result = await authenticator.authenticate(image_bytes, payload["sub"], "continuous")
    return {"continue_session": result.get("authenticated", False), "risk_score": result.get("risk_score")}

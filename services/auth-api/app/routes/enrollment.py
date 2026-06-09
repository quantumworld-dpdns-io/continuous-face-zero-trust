"""Enrollment routes."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form

router = APIRouter()


@router.post("/enroll")
async def enroll_face(
    face_images: list[UploadFile] = File(...),
    user_id: str = Form(...),
    tenant_id: str = Form("default"),
    device_id: str = Form(""),
):
    import httpx
    from app.config import settings

    images = [await img.read() for img in face_images]
    if len(images) < 2:
        return {"success": False, "error": "At least 2 face images required"}

    embeddings = []
    async with httpx.AsyncClient(base_url=settings.FACE_ML_URL, timeout=15.0) as client:
        for img_bytes in images:
            resp = await client.post("/api/v1/face/embed", content=img_bytes, headers={"Content-Type": "image/jpeg"})
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])

    import structlog
    logger = structlog.get_logger()
    logger.info("Face enrollment completed", user_id=user_id, face_count=len(images))

    return {
        "success": True,
        "enrollment_id": str(uuid.uuid4()),
        "face_count": len(images),
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
    }

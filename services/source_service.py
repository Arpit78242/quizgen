import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from models.study_source import StudySource
from models.user import User
from core.config import settings


ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
}


def _extract_text_from_pdf(file_path: str) -> str:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    return "\n\n".join(doc.page_content for doc in docs)


def _extract_text_from_docx(file_path: str) -> str:
    from langchain_community.document_loaders import Docx2txtLoader
    loader = Docx2txtLoader(file_path)
    docs = loader.load()
    return "\n\n".join(doc.page_content for doc in docs)


def _extract_text_from_image(file_path: str) -> str:
    try:
        from langchain_community.document_loaders import UnstructuredImageLoader
        loader = UnstructuredImageLoader(file_path)
        docs = loader.load()
        return "\n\n".join(doc.page_content for doc in docs)
    except Exception:
        # fallback to pytesseract directly
        import pytesseract
        from PIL import Image
        image = Image.open(file_path)
        return pytesseract.image_to_string(image)


async def save_file_source(db: Session, user: User, file: UploadFile) -> StudySource:
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOCX, PNG, JPEG"
        )

    source_type = ALLOWED_TYPES[content_type]

    # Save file to disk
    upload_dir = Path(settings.UPLOAD_DIR) / str(user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_ext = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_name

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB")

    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text using LangChain
    try:
        if source_type == "pdf":
            raw_text = _extract_text_from_pdf(str(file_path))
        elif source_type == "docx":
            raw_text = _extract_text_from_docx(str(file_path))
        elif source_type == "image":
            raw_text = _extract_text_from_image(str(file_path))
        else:
            raw_text = ""
    except Exception as e:
        raw_text = ""

    if not raw_text or len(raw_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Could not extract enough text from the file. Please try a different file.")

    source = StudySource(
        user_id=user.id,
        source_type=source_type,
        file_name=file.filename,
        file_path=str(file_path),
        raw_text=raw_text[:50000],  # cap at 50k chars to avoid prompt bloat
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def save_topic_source(db: Session, user: User, topic: str) -> StudySource:
    if not topic or len(topic.strip()) < 3:
        raise HTTPException(status_code=400, detail="Topic must be at least 3 characters")

    source = StudySource(
        user_id=user.id,
        source_type="topic",
        topic=topic.strip(),
        raw_text=None,  # AI generates from topic, not raw text
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_user_sources(db: Session, user: User):
    return db.query(StudySource).filter(StudySource.user_id == user.id).order_by(StudySource.created_at.desc()).all()


def delete_source(db: Session, user: User, source_id: str):
    source = db.query(StudySource).filter(
        StudySource.id == source_id,
        StudySource.user_id == user.id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Delete file if exists
    if source.file_path and os.path.exists(source.file_path):
        os.remove(source.file_path)

    db.delete(source)
    db.commit()

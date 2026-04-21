from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Query
from app.api.dependencies import get_db
from app.database.milvus_db import MilvusDB
from app.services.service import FileUploadService
from app.utils.embeddings import embed_query
from app.utils.file_parser import extract_elements_from_file
from pydantic import BaseModel
from app.utils.logger import logger

class ChatRequest(BaseModel):
    query: str
    top_k: int = 5

router = APIRouter()

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    db: MilvusDB = Depends(get_db),
):
    service = FileUploadService(db)

    # 1. Advanced Partitioning & Semantic Chunking
    elements = extract_elements_from_file(file)
    
    if not elements:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract any structured elements from the file",
        )

    base_metadata = {
        "content_type": file.content_type,
    }

    # 2. Enriched Ingestion
    result = service.upload_file_from_elements(
        filename=file.filename,
        elements=elements,
        base_metadata=base_metadata,
    )

    return {
        "message": "File processed with Unstructured and indexed successfully",
        **result
    }

@router.get("/search")
def search_documents(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(5, ge=1, le=10),
    db: MilvusDB = Depends(get_db),
):
    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query parameter cannot be empty",
        )

    service = FileUploadService(db)

    query_embedding = embed_query(query)
    results = service.search_reranked(query, query_embedding, top_k)
    
    return {
        "query": query,
        "mode": "high_accuracy_reranked",
        "top_k": top_k,
        "results": results,
    }
    
@router.post("/chat")
def chat_endpoint(
    payload: ChatRequest,
    db: MilvusDB = Depends(get_db),
):
    if not payload.query.strip():
        raise HTTPException(
            status_code=400,
            detail="query cannot be empty",
        )
    
    service=FileUploadService(db)
    
    query_embedding = embed_query(payload.query)
    
    response = service.chat(
        query = payload.query,
        query_embedding= query_embedding,
        top_k=payload.top_k,
    )
    logger.info("Chat endpoint called")
    return response
    
@router.delete("/delete")
def delete_file(
    filename: str = Query(..., description = "Filename to delete"),
    db: MilvusDB = Depends(get_db),
):
    service = FileUploadService(db)
    
    deleted_count = service.delete_file(filename)
    
    if deleted_count == 0:
        return{
            "status": "Not_found",
            "message": "No vectors found for this filename",
            "filename": filename,
        }
        
    return{
            "status": "success", 
            "message": "File vectors deleted successfuly", 
            "filename": filename,
            "vectors_deleted": deleted_count,
        }

from sqlalchemy.orm import Session
from app.database.sql_db import get_sql_db
from app.models.tutor_models import UserSession, QuizScore, UserWeakness
from app.services.tutor_service import TutorService
import uuid

class SessionCreate(BaseModel):
    pass

@router.post("/session")
def start_session(sql_db: Session = Depends(get_sql_db)):
    session_id = str(uuid.uuid4())
    db_session = UserSession(session_id=session_id)
    sql_db.add(db_session)
    sql_db.commit()
    sql_db.refresh(db_session)
    return {"session_id": session_id}

class QuizGenRequest(BaseModel):
    topic: str
    top_k: int = 5

@router.post("/quiz")
def generate_quiz(
    payload: QuizGenRequest,
    milvus_db: MilvusDB = Depends(get_db),
):
    service = TutorService(milvus_db)
    query_embedding = embed_query(payload.topic)
    return service.generate_quiz(payload.topic, query_embedding, payload.top_k)

class QuizSubmitRequest(BaseModel):
    session_id: str
    topic: str
    score: float
    total: int

@router.post("/quiz/submit")
def submit_quiz(
    payload: QuizSubmitRequest,
    sql_db: Session = Depends(get_sql_db)
):
    session = sql_db.query(UserSession).filter(UserSession.session_id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    quiz_score = QuizScore(
        session_id=session.id,
        topic=payload.topic,
        score=payload.score,
        total_questions=payload.total
    )
    sql_db.add(quiz_score)
    
    # Calculate weakness severity (percentage of incorrect answers)
    weakness_severity = 0.0
    if payload.total > 0:
        weakness_severity = (payload.total - payload.score) / payload.total
        
    # Update or create weakness
    weakness = sql_db.query(UserWeakness).filter(
        UserWeakness.session_id == session.id,
        UserWeakness.topic == payload.topic
    ).first()
    
    if weakness:
        weakness.severity = (weakness.severity + weakness_severity) / 2 # Moving average
    else:
        weakness = UserWeakness(
            session_id=session.id,
            topic=payload.topic,
            severity=weakness_severity
        )
        sql_db.add(weakness)
        
    sql_db.commit()
    return {"status": "success", "message": "Quiz stats saved!"}

@router.post("/chat/tutor")
def tutor_chat_endpoint(
    payload: ChatRequest,
    db: MilvusDB = Depends(get_db),
):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")
    
    service = TutorService(db)
    query_embedding = embed_query(payload.query)
    
    response = service.chat_tutor(
        query=payload.query,
        query_embedding=query_embedding,
        top_k=payload.top_k,
    )
    return response

@router.get("/progress")
def get_progress(
    session_id: str = Query(...),
    sql_db: Session = Depends(get_sql_db)
):
    session = sql_db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    scores = sql_db.query(QuizScore).filter(QuizScore.session_id == session.id).all()
    weaknesses = sql_db.query(UserWeakness).filter(UserWeakness.session_id == session.id).all()
    
    return {
        "scores": [{"topic": s.topic, "score": s.score, "total": s.total_questions, "date": s.created_at} for s in scores],
        "weaknesses": [{"topic": w.topic, "severity": w.severity} for w in weaknesses]
    }

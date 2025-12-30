"""
FitLife AI - FastAPI 백엔드
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

from ..rag import FitLifeRAG
from ..xai import HealthExplainer
from ..config import API_HOST, API_PORT


# FastAPI 앱 생성
app = FastAPI(
    title="FitLife AI API",
    description="AI 기반 건강 상태 분석 및 맞춤 식단/운동 추천 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 인스턴스
rag_system = None
explainer = None


# 요청 스키마 정의
class UserProfile(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    health_conditions: Optional[List[str]] = []


class HealthData(BaseModel):
    protein_intake: Optional[float] = 0
    carb_intake: Optional[float] = 0
    fat_intake: Optional[float] = 0
    calories: Optional[float] = 0
    sleep_hours: Optional[float] = 7
    exercise_days: Optional[int] = 0
    stress_level: Optional[int] = 5
    water_intake: Optional[float] = 0
    height: Optional[float] = 170
    weight: Optional[float] = 70


class ChatRequest(BaseModel):
    message: str
    profile: Optional[UserProfile] = None
    health_data: Optional[HealthData] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict]
    confidence: float
    health_analysis: Optional[Dict] = None


# 시작 이벤트
@app.on_event("startup")
async def startup_event():
    global rag_system, explainer
    try:
        rag_system = FitLifeRAG()
        explainer = HealthExplainer()
        print("✅ FitLife AI 시스템 초기화 완료")
    except Exception as e:
        print(f"⚠️ 초기화 중 오류 (API 키 확인 필요): {e}")


# API 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "FitLife AI API",
        "version": "1.0.0",
        "endpoints": ["/chat", "/analyze", "/health"]
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG 기반 건강 상담 챗봇
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="시스템 초기화 중입니다")
    
    # 프로필 변환
    profile_dict = request.profile.dict() if request.profile else None
    
    # RAG 쿼리
    result = rag_system.query(
        user_query=request.message,
        user_profile=profile_dict
    )
    
    # 건강 데이터가 있으면 분석 추가
    health_analysis = None
    if request.health_data:
        health_analysis = explainer.analyze_health_factors(request.health_data.dict())
    
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
        health_analysis=health_analysis
    )


@app.post("/analyze")
async def analyze_health(health_data: HealthData):
    """
    건강 데이터 분석 및 XAI 설명 생성
    """
    if not explainer:
        raise HTTPException(status_code=503, detail="시스템 초기화 중입니다")
    
    analysis = explainer.analyze_health_factors(health_data.dict())
    explanation = explainer.generate_explanation(analysis)
    
    return {
        "analysis": analysis,
        "explanation": explanation
    }


@app.get("/stats")
async def get_stats():
    """
    지식베이스 통계
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="시스템 초기화 중입니다")
    
    return rag_system.kb.get_stats()


def run_server():
    """서버 실행"""
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    run_server()

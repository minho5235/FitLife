"""
FitLife AI 설정 파일
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트 경로
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ChromaDB 설정
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db"))
COLLECTION_NAME = "fitlife_knowledge"

# 임베딩 모델 설정
EMBEDDING_MODEL = "models/embedding-001"  # Google 임베딩 모델

# LLM 설정
LLM_MODEL = "gemini-1.5-flash"  # 또는 "gemini-1.5-pro"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2048

# RAG 설정
RAG_TOP_K = 5  # 검색할 문서 수
RAG_SCORE_THRESHOLD = 0.7  # 유사도 임계값

# API 설정
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# 카테고리 정의
FOOD_CATEGORIES = ["고단백", "저탄수화물", "저지방", "고섬유질", "비타민", "미네랄"]
EXERCISE_CATEGORIES = ["유산소", "근력", "유연성", "균형", "HIIT"]
HEALTH_GOALS = ["다이어트", "근육증가", "체력향상", "건강유지", "피로회복"]

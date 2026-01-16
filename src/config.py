"""
FitLife AI 통합 설정 파일
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ==========================================
# 1. 경로 설정 (Path Configuration)
# ==========================================
# config.py가 src 폴더 안에 있다고 가정하고 루트 경로 계산
ROOT_DIR = Path(__file__).parent.parent 
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# ==========================================
# 2. API 키 및 시크릿 (Secrets)
# ==========================================
# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Supabase (Vector DB)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 공공데이터포털 (식품안전나라)
FOOD_SAFETY_API_KEY = os.getenv("FOOD_SAFETY_API_KEY")

# ==========================================
# 3. 데이터베이스 설정 (Supabase)
# ==========================================
VECTOR_DB_TABLE = "documents"          # 우리가 만든 테이블 이름
VECTOR_DB_QUERY_FUNC = "match_documents" # 우리가 만든 검색 함수 이름

# ==========================================
# 4. AI 모델 설정 (Models)
# ==========================================
# 임베딩 모델 (KnowledgeBase 클래스와 일치시켜야 함)
# 로컬에서 한국어 성능이 가장 좋은 모델 중 하나
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# LLM 설정 (Gemini)
LLM_MODEL = "gemini-2.5-flash"  # 가성비/속도 최적화 모델
LLM_TEMPERATURE = 0.7           # 0~1 사이 (창의성 조절)
LLM_MAX_TOKENS = 4096

# ==========================================
# 5. RAG (검색 증강 생성) 설정
# ==========================================
RAG_TOP_K = 5              # 검색할 문서 수 (5개 정도가 적당)
RAG_SCORE_THRESHOLD = 0.4  # 유사도 임계값 (0~1, 낮을수록 더 많이 검색됨)

# ==========================================
# 6. API 서버 설정 (FastAPI)
# ==========================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# ==========================================
# 7. 앱 상수 (Constants)
# ==========================================
FOOD_CATEGORIES = ["고단백", "저탄수화물", "저지방", "키토제닉", "비건"]
EXERCISE_CATEGORIES = ["홈트레이닝", "유산소", "웨이트", "스트레칭", "요가"]
HEALTH_GOALS = ["다이어트", "근육량증가", "체력증진", "체형교정"]
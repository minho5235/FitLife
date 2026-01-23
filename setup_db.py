import psycopg2
import os
from dotenv import load_dotenv

# 1. .env 파일 로드
load_dotenv()

# 2. .env에서 비밀번호 가져오기
db_password = os.getenv("DatabasePassword")

# 3. DB 연결 주소 설정
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL and db_password:
    DB_URL = f"postgresql://postgres:{db_password}@sutfbthohnlosesbtolz.supabase.co:5432/postgres"

if not DB_URL:
    raise ValueError("❌ 데이터베이스 연결 정보를 찾을 수 없습니다 (.env 확인 필요)")

def reset_table():
    try:
        print("🔌 데이터베이스 연결 중...")
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True # 자동 커밋 설정
        cur = conn.cursor()

        # 1. 기존 테이블 삭제 (DROP)
        print("🗑️ 기존 'users' 테이블 삭제 중...")
        cur.execute("DROP TABLE IF EXISTS users;")
        
        # 2. 테이블 새로 생성 (notes 컬럼 포함)
        print("🔨 'users' 테이블 새로 생성 중...")
        create_query = """
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            gender TEXT,
            height DOUBLE PRECISION,
            weight DOUBLE PRECISION,
            diseases TEXT,
            allergies TEXT,
            notes TEXT,  -- ★ 특이사항 컬럼 포함됨
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        cur.execute(create_query)
        
        print("✅ 'users' 테이블 리셋(재생성) 완료!")
        
        # 확인용: 컬럼 정보 조회
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users';
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"📋 생성된 컬럼 목록: {columns}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    reset_table()
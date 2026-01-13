import psycopg2
import os
from dotenv import load_dotenv

# 1. .env 파일 로드
load_dotenv()

# 2. .env에서 비밀번호 가져오기 (이미지에서 변수명이 DatabasePassword 였음)
db_password = os.getenv("DatabasePassword")

# 3. DB 연결 주소 조합 (f-string 사용)
# 비밀번호가 없으면 에러를 띄우도록 체크
if not db_password:
    raise ValueError("❌ .env 파일에서 'DatabasePassword'를 찾을 수 없습니다.")

DB_URL = f"postgresql://postgres:{db_password}@sutfbthohnlosesbtolz.supabase.co:5432/postgres"
DB_URL = os.getenv("DATABASE_URL")

def create_table():
    try:
        print("🔌 데이터베이스 연결 중...")
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # 테이블 생성 쿼리
        create_query = """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            gender TEXT,
            height DOUBLE PRECISION,
            weight DOUBLE PRECISION,
            diseases TEXT,
            allergies TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        cur.execute(create_query)
        conn.commit()
        
        print("✅ 'users' 테이블 생성 완료!")
        
        # 확인용
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        print(f"📋 현재 테이블 목록: {cur.fetchall()}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    create_table()
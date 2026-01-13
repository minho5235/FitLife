# src/auth/manager.py
import os
from supabase import create_client, Client
from typing import Optional, Dict
import hashlib

# .env 파일이나 Streamlit Secrets에서 키를 가져와야 안전함
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

class UserManager:
    def __init__(self):
        # 클라우드 DB 연결
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def _hash_pw(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username, password, name, age, gender, height, weight):
        try:
            data = {
                "username": username,
                "password_hash": self._hash_pw(password),
                "name": name,
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
                "diseases": "",
                "allergies": ""
            }
            # Supabase에 데이터 삽입
            self.supabase.table("users").insert(data).execute()
            return True
        except Exception as e:
            print(f"회원가입 에러: {e}")
            return False

    def login(self, username, password) -> Optional[Dict]:
        try:
            # 아이디와 해시된 비번으로 검색
            pw_hash = self._hash_pw(password)
            response = self.supabase.table("users").select("*")\
                .eq("username", username)\
                .eq("password_hash", pw_hash)\
                .execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                # 리스트 형태로 변환이 필요한 필드 처리
                if user_data.get("diseases"):
                    user_data["diseases"] = user_data["diseases"].split(",")
                else:
                    user_data["diseases"] = []
                    
                if user_data.get("allergies"):
                    user_data["allergies"] = user_data["allergies"].split(",")
                else:
                    user_data["allergies"] = []
                    
                return user_data
            return None
        except Exception as e:
            print(f"로그인 에러: {e}")
            return None
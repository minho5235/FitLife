# test_gemini.py
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# API 키 확인
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API 키 로드: {'✅ 성공' if api_key else '❌ 실패'}")

# Gemini 테스트
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key
)

response = llm.invoke("안녕! 건강 관리 AI 어시스턴트야?")
print("\n🤖 Gemini 응답:")
print(response.content)
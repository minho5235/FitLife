"""FitLife AI - 통합 테스트"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_config():
    print("1️⃣ Config 테스트...")
    from src.config import GOOGLE_API_KEY
    assert GOOGLE_API_KEY, "GOOGLE_API_KEY가 설정되지 않았습니다"
    print("   ✅ API 키 설정됨")

def test_user_profile():
    print("2️⃣ UserProfile 테스트...")
    from src.models.user_profile import UserProfile
    profile = UserProfile(age=30, gender="남성", height=175, weight=70)
    assert profile.bmi == 22.9
    assert profile.bmi_status == "정상"
    print(f"   ✅ BMI: {profile.bmi} ({profile.bmi_status})")
    print(f"   ✅ 권장 칼로리: {profile.recommended_calories}kcal")

def test_knowledge_base():
    print("3️⃣ KnowledgeBase 테스트...")
    from src.rag.knowledge_base import KnowledgeBase
    kb = KnowledgeBase()
    stats = kb.get_stats()
    print(f"   ✅ 문서 수: {stats.get('total_documents', 0)}개")

def test_rag():
    print("4️⃣ RAG 테스트...")
    from src.rag.chain import FitLifeRAG
    from src.models.user_profile import UserProfile
    rag = FitLifeRAG()
    profile = UserProfile(age=30, gender="남성", height=175, weight=70, goal="체중감량")
    result = rag.query("다이어트에 좋은 음식 추천해줘", profile)
    print(f"   ✅ 응답 길이: {len(result.get('answer', ''))}자")

def test_xai():
    print("5️⃣ XAI 테스트...")
    from src.xai.explainer import HealthExplainer
    xai = HealthExplainer()
    health_data = {"protein_intake": 60, "carb_intake": 300, "fat_intake": 65, "calories": 2000, "sleep_hours": 7, "exercise_days": 3, "stress_level": 5, "water_intake": 2, "height": 175, "weight": 70}
    result = xai.analyze_health_factors(health_data)
    print(f"   ✅ 건강 점수: {result['health_score']}점")

def main():
    print("=" * 50)
    print("🏃 FitLife AI - 통합 테스트")
    print("=" * 50)
    
    tests = [test_config, test_user_profile, test_knowledge_base, test_rag, test_xai]
    passed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"   ❌ 실패: {e}")
    
    print("=" * 50)
    print(f"결과: {passed}/{len(tests)} 통과")

if __name__ == "__main__":
    main()

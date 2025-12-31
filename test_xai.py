# test_xai.py
from dotenv import load_dotenv
load_dotenv()

from src.xai.explainer import HealthExplainer

print("🔬 XAI 건강 분석 테스트")
print("=" * 50)

# XAI 시스템 초기화
xai = HealthExplainer()

# 테스트 건강 데이터 (키 이름 수정!)
health_data = {
    "protein_intake": 50,
    "carb_intake": 350,
    "fat_intake": 80,
    "calories": 2500,
    "sleep_hours": 5,
    "exercise_days": 1,
    "stress_level": 8,
    "water_intake": 1.0,
    "height": 175,
    "weight": 78
}

print("\n📊 입력 데이터:")
print(f"   - 키: {health_data['height']}cm")
print(f"   - 체중: {health_data['weight']}kg")
print(f"   - 단백질: {health_data['protein_intake']}g")
print(f"   - 탄수화물: {health_data['carb_intake']}g")
print(f"   - 지방: {health_data['fat_intake']}g")
print(f"   - 칼로리: {health_data['calories']}kcal")
print(f"   - 수면: {health_data['sleep_hours']}시간")
print(f"   - 운동: 주 {health_data['exercise_days']}회")
print(f"   - 스트레스: {health_data['stress_level']}/10")
print(f"   - 수분: {health_data['water_intake']}L")

print("\n" + "-" * 50)
print("🔍 분석 중...")

# 분석 실행
result = xai.analyze_health_factors(health_data)

# 자연어 설명 생성
explanation = xai.generate_explanation(result)

print("\n" + explanation)

print("\n" + "=" * 50)
print("✅ XAI 테스트 완료!")

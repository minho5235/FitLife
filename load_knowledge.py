# load_knowledge.py
import json
import time  # 추가!
from dotenv import load_dotenv

load_dotenv()

from src.rag.knowledge_base import KnowledgeBase

# 지식베이스 초기화
print("📚 지식베이스 초기화 중...")
kb = KnowledgeBase()

# 1. 음식 데이터 로드
print("\n🍽️ 음식 데이터 로딩...")
with open("data/raw/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

# 10개씩 나눠서 처리 (Rate Limit 방지)
batch_size = 10
for i in range(0, len(foods), batch_size):
    batch = foods[i:i+batch_size]
    food_docs = []
    
    for food in batch:
        content = f"""
음식명: {food['name']}
카테고리: {food['category']}
칼로리: {food['calories']}kcal (100g당)
단백질: {food['protein']}g
탄수화물: {food['carbs']}g
지방: {food['fat']}g
설명: {food['description']}
효능: {', '.join(food['benefits'])}
"""
        food_docs.append({
            "title": food['name'],
            "content": content,
            "source": food['source']
        })
    
    kb.add_documents(documents=food_docs, category="food")
    print(f"   음식 {i+len(batch)}/{len(foods)} 완료")
    time.sleep(5)  # 5초 대기

# 2. 운동 데이터 로드
print("\n🏋️ 운동 데이터 로딩...")
with open("data/raw/exercises.json", "r", encoding="utf-8") as f:
    exercises = json.load(f)

for i in range(0, len(exercises), batch_size):
    batch = exercises[i:i+batch_size]
    exercise_docs = []
    
    for ex in batch:
        content = f"""
운동명: {ex['name']}
카테고리: {ex['category']}
시간당 칼로리 소모: {ex['calories_per_hour']}kcal
강도: {ex['intensity']}
타겟 근육: {', '.join(ex['target_muscles'])}
설명: {ex['description']}
효과: {', '.join(ex['benefits'])}
추천 대상: {', '.join(ex['suitable_for'])}
"""
        exercise_docs.append({
            "title": ex['name'],
            "content": content,
            "source": ex['source']
        })
    
    kb.add_documents(documents=exercise_docs, category="exercise")
    print(f"   운동 {i+len(batch)}/{len(exercises)} 완료")
    time.sleep(5)  # 5초 대기

# 3. 통계 확인
print("\n📊 지식베이스 통계:")
stats = kb.get_stats()
print(f"   총 문서 수: {stats['total_documents']}개")

# 4. 검색 테스트
print("\n🔍 검색 테스트: '단백질이 많은 음식'")
results = kb.search("단백질이 많은 음식", top_k=3)
for i, doc in enumerate(results, 1):
    print(f"\n   [{i}] {doc['metadata']['title']}")
    print(f"       유사도: {doc['score']:.2f}")

print("\n✨ 지식베이스 구축 완료!")
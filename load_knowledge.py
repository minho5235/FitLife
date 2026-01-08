"""
FitLife AI - 지식베이스 구축 스크립트 v2.1
전체 데이터 로드 (국민체력100 500개 전체)
"""
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.rag.knowledge_base import KnowledgeBase


def load_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("🏃 FitLife AI - 지식베이스 구축 v2.1")
    print("=" * 60)
    
    kb = KnowledgeBase()
    
    data_path = project_root / "data"
    raw_path = data_path / "raw"
    processed_path = data_path / "processed"
    
    total_added = 0
    
    # 1. 음식 데이터
    foods_file = raw_path / "foods.json"
    if foods_file.exists():
        print("\n📦 음식 데이터 로딩...")
        foods = load_json_file(foods_file)
        
        documents = []
        for food in foods:
            content = f"{food['name']}: 칼로리 {food.get('calories', 0)}kcal, 단백질 {food.get('protein', 0)}g, 탄수화물 {food.get('carbs', 0)}g, 지방 {food.get('fat', 0)}g, 당류 {food.get('sugar', 0)}g, 나트륨 {food.get('sodium', 0)}mg. "
            if food.get('benefits'):
                content += f"효능: {', '.join(food['benefits'])}. "
            if food.get('description'):
                content += food['description']
            if food.get('health_tags'):
                content += f" 태그: {', '.join(food['health_tags'])}"
            
            documents.append({
                "content": content,
                "metadata": {
                    "category": "food",
                    "title": food['name'],
                    "source": food.get('source', '식품안전나라'),
                    "health_tags": ",".join(food.get('health_tags', []))
                }
            })
        
        kb.add_documents(documents, category="food")
        total_added += len(documents)
        print(f"✅ 음식 데이터: {len(foods)}개 완료")
    
    # 2. 운동 데이터
    exercises_file = raw_path / "exercises.json"
    if exercises_file.exists():
        print("\n🏋️ 운동 데이터 로딩...")
        exercises = load_json_file(exercises_file)
        
        documents = []
        for ex in exercises:
            content = f"{ex['name']}: {ex.get('category', '')} 운동, 강도 {ex.get('intensity', '보통')}, 시간당 {ex.get('calories_per_hour', 0)}kcal 소모. "
            if ex.get('target_muscles'):
                content += f"주요 부위: {', '.join(ex['target_muscles'])}. "
            if ex.get('benefits'):
                content += f"효과: {', '.join(ex['benefits'])}. "
            if ex.get('description'):
                content += ex['description']
            
            documents.append({
                "content": content,
                "metadata": {
                    "category": "exercise",
                    "title": ex['name'],
                    "source": ex.get('source', 'ACSM'),
                    "intensity": ex.get('intensity', '보통'),
                    "health_tags": ",".join(ex.get('health_tags', []))
                }
            })
        
        kb.add_documents(documents, category="exercise")
        total_added += len(documents)
        print(f"✅ 운동 데이터: {len(exercises)}개 완료")
    
    # 3. 국민체력100 (전체)
    nfa_file = processed_path / "exercises_nfa.json"
    if nfa_file.exists():
        print("\n🏃 국민체력100 운동 데이터 로딩 (전체)...")
        nfa_exercises = load_json_file(nfa_file)
        
        documents = []
        for ex in nfa_exercises:  # 전체 로드
            content = f"{ex['name']}: {ex.get('category', '')} 운동, {ex.get('phase', '')} 단계, 강도 {ex.get('intensity', '보통')}, 시간당 약 {ex.get('calories_per_hour', 200)}kcal 소모. "
            if ex.get('health_tags'):
                content += f"효과: {', '.join(ex['health_tags'])}. "
            if ex.get('suitable_for'):
                content += f"대상: {', '.join(ex['suitable_for'])}. "
            content += f"(인기도: {ex.get('popularity', 0)})"
            
            documents.append({
                "content": content,
                "metadata": {
                    "category": "exercise",
                    "title": ex['name'],
                    "source": "국민체력100",
                    "phase": ex.get('phase', ''),
                    "intensity": ex.get('intensity', '보통'),
                    "health_tags": ",".join(ex.get('health_tags', []))
                }
            })
        
        kb.add_documents(documents, category="exercise")
        total_added += len(documents)
        print(f"✅ 국민체력100 데이터: {len(documents)}개 완료")
    
    # 완료
    print("\n" + "=" * 60)
    print(f"🎉 지식베이스 구축 완료!")
    print(f"📊 총 문서 수: {total_added}개")
    
    stats = kb.get_stats()
    print(f"📈 ChromaDB 문서: {stats.get('total_documents', 'N/A')}개")
    
    # 테스트
    print("\n🔍 테스트 검색: '다이어트 운동'")
    results = kb.search("다이어트에 좋은 유산소 운동", top_k=3)
    for r in results:
        title = r.get('metadata', {}).get('title', '')
        source = r.get('metadata', {}).get('source', '')
        print(f"   - {title} ({source})")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

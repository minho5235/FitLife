# test_rag_chat.py
from dotenv import load_dotenv
load_dotenv()

from src.rag.chain import FitLifeRAG

print("🚀 FitLife AI RAG 시스템 시작...")
print("=" * 50)

# RAG 시스템 초기화
rag = FitLifeRAG()

# 테스트 질문들
questions = [
    "단백질이 많은 음식 추천해줘",
    "다이어트에 좋은 운동은 뭐야?",
    "근육을 키우려면 어떻게 해야해?"
]

for q in questions:
    print(f"\n👤 질문: {q}")
    print("-" * 40)
    
    response = rag.query(q)  # chat → query로 변경!
    
    print(f"🤖 답변:\n{response['answer']}")
    print(f"\n📚 참고 자료:")
    for src in response['sources'][:3]:
        print(f"   - {src['metadata']['title']} (유사도: {src['score']:.2f})")
    print(f"\n💯 신뢰도: {response['confidence']:.2f}")
    print("=" * 50)

print("\n✅ RAG 테스트 완료!")
"""
RAG 체인 - LLM과 지식베이스 연동
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Optional

from .knowledge_base import KnowledgeBase
from ..config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class FitLifeRAG:
    """FitLife AI RAG 시스템"""
    
    def __init__(self):
        # 지식베이스 초기화
        self.kb = KnowledgeBase()
        
        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS
        )
        
        # 시스템 프롬프트
        self.system_prompt = """당신은 FitLife AI, 건강 관리 전문 AI 어시스턴트입니다.

역할:
- 사용자의 건강 상태를 분석하고 맞춤 식단과 운동을 추천합니다.
- 추천할 때 반드시 근거와 출처를 함께 제시합니다.
- 의료적 진단은 하지 않으며, 건강 관리 조언만 제공합니다.

응답 형식:
1. 건강 상태 분석
2. 맞춤 추천 (식단/운동)
3. 추천 이유 및 근거
4. 참고 출처

주의사항:
- 항상 친절하고 이해하기 쉽게 설명합니다.
- 확실하지 않은 정보는 명시합니다.
- 심각한 증상은 전문의 상담을 권유합니다."""

    def query(
        self, 
        user_query: str, 
        user_profile: Optional[Dict] = None,
        search_categories: Optional[List[str]] = None
    ) -> Dict:
        """
        사용자 질문에 대한 RAG 기반 응답 생성
        
        Args:
            user_query: 사용자 질문
            user_profile: 사용자 프로필 (키, 몸무게, 목표 등)
            search_categories: 검색할 카테고리 필터
            
        Returns:
            {
                "answer": "응답 텍스트",
                "sources": [검색된 문서들],
                "confidence": 신뢰도
            }
        """
        # 1. 지식베이스 검색
        search_results = []
        if search_categories:
            for category in search_categories:
                results = self.kb.search(user_query, top_k=3, category=category)
                search_results.extend(results)
        else:
            search_results = self.kb.search(user_query, top_k=5)
        
        # 2. 컨텍스트 구성
        context = self._build_context(search_results)
        
        # 3. 사용자 프로필 정보 추가
        profile_info = self._format_profile(user_profile) if user_profile else ""
        
        # 4. 프롬프트 구성
        user_message = f"""
{profile_info}

[사용자 질문]
{user_query}

[참고 자료]
{context}

위 정보를 바탕으로 사용자에게 맞춤 건강 조언을 제공해주세요.
반드시 참고 자료의 출처를 명시하고, 추천 이유를 설명해주세요.
"""
        
        # 5. LLM 호출
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        
        # 6. 결과 반환
        return {
            "answer": response.content,
            "sources": search_results,
            "confidence": self._calculate_confidence(search_results)
        }
    
    def _build_context(self, search_results: List[Dict]) -> str:
        """검색 결과를 컨텍스트 문자열로 변환"""
        if not search_results:
            return "관련 자료를 찾지 못했습니다."
        
        context_parts = []
        for i, result in enumerate(search_results, 1):
            source = result["metadata"].get("source", "출처 미상")
            title = result["metadata"].get("title", "")
            content = result["content"]
            score = result["score"]
            
            context_parts.append(
                f"[자료 {i}] (출처: {source}, 유사도: {score:.2f})\n"
                f"{title}\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def _format_profile(self, profile: Dict) -> str:
        """사용자 프로필 포맷팅"""
        parts = ["[사용자 정보]"]
        
        if "age" in profile:
            parts.append(f"- 나이: {profile['age']}세")
        if "gender" in profile:
            parts.append(f"- 성별: {profile['gender']}")
        if "height" in profile:
            parts.append(f"- 키: {profile['height']}cm")
        if "weight" in profile:
            parts.append(f"- 체중: {profile['weight']}kg")
        if "goal" in profile:
            parts.append(f"- 목표: {profile['goal']}")
        if "activity_level" in profile:
            parts.append(f"- 활동량: {profile['activity_level']}")
        if "health_conditions" in profile:
            parts.append(f"- 건강 상태: {', '.join(profile['health_conditions'])}")
        
        return "\n".join(parts)
    
    def _calculate_confidence(self, search_results: List[Dict]) -> float:
        """검색 결과 기반 신뢰도 계산"""
        if not search_results:
            return 0.0
        
        # 상위 결과들의 평균 유사도
        scores = [r["score"] for r in search_results[:3]]
        return sum(scores) / len(scores) if scores else 0.0


# 테스트용
if __name__ == "__main__":
    rag = FitLifeRAG()
    
    result = rag.query(
        user_query="요즘 피곤하고 근육이 빠지는 느낌이에요. 뭘 먹고 운동해야 할까요?",
        user_profile={
            "age": 35,
            "gender": "남성",
            "height": 175,
            "weight": 78,
            "goal": "체력향상"
        }
    )
    
    print("=" * 50)
    print(result["answer"])
    print("=" * 50)
    print(f"신뢰도: {result['confidence']:.2f}")

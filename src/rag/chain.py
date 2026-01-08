"""
RAG 체인 - LLM과 지식베이스 연동
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Optional, Union

from .knowledge_base import KnowledgeBase
from ..config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS


class FitLifeRAG:
    """FitLife AI RAG 시스템"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS
        )
        
        self.system_prompt = """당신은 FitLife AI, 건강 관리 전문 AI 어시스턴트입니다.

역할:
- 사용자의 건강 상태를 분석하고 맞춤 식단과 운동을 추천합니다.
- 추천할 때 반드시 근거와 출처를 함께 제시합니다.
- 의료적 진단은 하지 않으며, 건강 관리 조언만 제공합니다.

응답 형식:
1. 건강 상태 분석
2. 맞춤 추천 (식단/운동)
3. 추천 이유 및 근거

주의사항:
- 항상 친절하고 이해하기 쉽게 설명합니다.
- 확실하지 않은 정보는 명시합니다.
- 심각한 증상은 전문의 상담을 권유합니다."""

    def query(
        self, 
        user_query: str, 
        user_profile: Optional[Union[Dict, object]] = None,
        search_categories: Optional[List[str]] = None
    ) -> Dict:
        """
        사용자 질문에 대한 RAG 기반 응답 생성
        
        Args:
            user_query: 사용자 질문
            user_profile: 사용자 프로필 (Dict 또는 UserProfile 객체)
            search_categories: 검색할 카테고리 필터
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
            source = result.get("metadata", {}).get("source", "출처 미상")
            title = result.get("metadata", {}).get("title", "")
            content = result.get("content", "")
            score = result.get("score", 0)
            
            context_parts.append(
                f"[자료 {i}] (출처: {source}, 유사도: {score:.2f})\n"
                f"{title}\n{content}"
            )
        
        return "\n\n".join(context_parts)
    
    def _format_profile(self, profile: Union[Dict, object]) -> str:
        """사용자 프로필 포맷팅 - Dict 또는 UserProfile 객체 모두 지원"""
        parts = ["[사용자 정보]"]
        
        # Dict인지 객체인지 확인
        if isinstance(profile, dict):
            # 딕셔너리인 경우
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
            if "diseases" in profile and profile["diseases"]:
                parts.append(f"- 질환: {', '.join(profile['diseases'])}")
            if "allergies" in profile and profile["allergies"]:
                parts.append(f"- 알러지: {', '.join(profile['allergies'])}")
        else:
            # UserProfile 객체인 경우
            if hasattr(profile, 'age'):
                parts.append(f"- 나이: {profile.age}세")
            if hasattr(profile, 'gender'):
                parts.append(f"- 성별: {profile.gender}")
            if hasattr(profile, 'height'):
                parts.append(f"- 키: {profile.height}cm")
            if hasattr(profile, 'weight'):
                parts.append(f"- 체중: {profile.weight}kg")
            if hasattr(profile, 'bmi'):
                parts.append(f"- BMI: {profile.bmi} ({profile.bmi_status})")
            if hasattr(profile, 'goal'):
                parts.append(f"- 목표: {profile.goal}")
            if hasattr(profile, 'activity_level'):
                parts.append(f"- 활동량: {profile.activity_level}")
            if hasattr(profile, 'diseases') and profile.diseases:
                parts.append(f"- 질환: {', '.join(profile.diseases)}")
            if hasattr(profile, 'allergies') and profile.allergies:
                parts.append(f"- 알러지: {', '.join(profile.allergies)}")
            if hasattr(profile, 'recommended_calories'):
                parts.append(f"- 권장 칼로리: {profile.recommended_calories}kcal")
        
        return "\n".join(parts)
    
    def _calculate_confidence(self, search_results: List[Dict]) -> float:
        """검색 결과 기반 신뢰도 계산"""
        if not search_results:
            return 0.0
        
        scores = [r.get("score", 0) for r in search_results[:3]]
        return sum(scores) / len(scores) if scores else 0.0
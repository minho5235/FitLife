"""
RAG 체인 - LLM과 지식베이스 연동 (XAI 심층 분석 + 풍성한 식단 버전)
"""
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Optional, Union

from .knowledge_base import KnowledgeBase
from ..config import GOOGLE_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

class FitLifeRAG:
    """FitLife AI RAG 시스템"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        
        # 사용자가 성공한 Gemini 2.5 모델 유지
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3, # 설명을 위해 창의성 약간 높임
            max_output_tokens=4096 # 답변 길게 하도록 토큰 늘림
        )

    def query(
        self, 
        user_query: str, 
        user_profile: Optional[Union[Dict, object]] = None,
        search_categories: Optional[List[str]] = None,
        mode: str = "general" # 모드 부활
    ) -> Dict:
        """
        사용자 질문에 대한 RAG 기반 응답 생성 (XAI 강화)
        """
        
        # 1. [검색어 확장] AI가 더 똑똑하게 찾도록 키워드 추가
        enhanced_query = user_query
        target_goal = ""
        if isinstance(user_profile, dict): target_goal = user_profile.get("goal", "")
        elif hasattr(user_profile, "goal"): target_goal = user_profile.goal
            
        if mode == "food":
            enhanced_query += f" {target_goal} 고단백 저지방 식이섬유 영양성분 효능"
        elif mode == "exercise":
            enhanced_query += f" {target_goal} 운동효과 자극부위 주의사항"

        # 2. [데이터 확보] 5개는 너무 적음 -> 15개로 늘림
        search_results_raw = []
        if search_categories:
            for category in search_categories:
                # 15개 정도면 식단 짜기에 충분하고 속도도 괜찮음
                results = self.kb.search(enhanced_query, top_k=30, category=category)
                search_results_raw.extend(results)
        else:
            search_results_raw = self.kb.search(enhanced_query, top_k=15)
        
        # 3. 컨텍스트 구성
        context = self._build_context(search_results_raw)
        profile_info = self._format_profile(user_profile) if user_profile else ""
        
        # 4. [XAI 프롬프트] 상세 설명을 강제하는 프롬프트 생성
        system_prompt, user_message = self._create_xai_prompt(mode, profile_info, user_query, context)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        # 5. LLM 호출 (재시도 로직 포함 - 429 에러 방지)
        response_content = ""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                response_content = response.content
                break 
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < max_retries - 1:
                        time.sleep(10) # 10초 대기
                        continue
                    else:
                        response_content = "⚠️ 사용량이 많아 답변 생성에 실패했습니다. 아래 검색 결과를 참고해주세요."
                else:
                    response_content = f"오류 발생: {e}"
                    break
        
        # 6. 결과 반환
        formatted_sources = []
        for doc, score in search_results_raw:
            source_item = doc.metadata.copy()
            source_item['content'] = doc.page_content
            source_item['score'] = score
            formatted_sources.append(source_item)

        return {
            "answer": response_content,
            "sources": formatted_sources,
            "confidence": self._calculate_confidence(search_results_raw)
        }
    
    def _create_xai_prompt(self, mode, profile_info, query, context):
        """
        ★ [핵심] AI에게 '설명 가능한 AI(XAI)' 역할을 부여하는 프롬프트
        """
        
        base_instruction = """
        [지침]
        1. 반드시 [참고 자료]에 있는 데이터만 사용하세요.
        2. 추천하는 이유를 '영양학적 관점'과 '사용자 건강 상태'에 맞춰 상세히 설명하세요.
        3. 각 음식/운동마다 기대 효과를 구체적으로 서술하세요.
        4. 같은 음식/운동을 중복해서 추천하지 마십시오.
        """

        if mode == "food":
            system_prompt = f"""당신은 '임상 영양 전문 AI'입니다. 
            단순히 메뉴만 나열하지 말고, **왜 이 음식이 사용자의 목표(다이어트/근육 등)와 질환(당뇨 등)에 좋은지** 의학/영양학적 근거를 들어 설명하세요.
            
            [출력 형식]
            1. 📊 **사용자 건강 분석**: 현재 상태와 식단 전략 요약
            2. 🍽️ **맞춤 식단 제안**: 아침/점심/저녁/간식 (칼로리 포함)
            3. 💡 **영양 분석 (XAI)**: 
               - 선정 이유: (예: 당뇨가 있으므로 GI 지수가 낮은 현미를 선택했습니다)
               - 기대 효과: (예: 단백질 20g은 근육 회복을 돕습니다)
            
            {base_instruction}
            """
        elif mode == "exercise":
            system_prompt = f"""당신은 '전문 스포츠 의학 AI'입니다.
            단순히 운동만 나열하지 말고, **왜 이 운동이 사용자에게 필요한지** 생리학적 근거를 들어 설명하세요.
            
            [출력 형식]
            1. 📊 **운동 능력 분석**: 사용자 상태 요약
            2. 💪 **오늘의 루틴**: 운동 종목, 세트, 횟수
            3. 💡 **운동 효과 분석 (XAI)**:
               - 선정 이유: (예: 관절이 약하므로 저충격 운동을 선택했습니다)
               - 타겟 부위: (예: 대흉근과 삼두근을 자극합니다)
            
            {base_instruction}
            """
        else:
            system_prompt = f"당신은 FitLife AI입니다. 상세하고 친절하게 답변하세요. {base_instruction}"

        user_message = f"{profile_info}\n[질문]: {query}\n[참고 자료]:\n{context}"
        return system_prompt, user_message

    def _build_context(self, search_results: List) -> str:
        if not search_results: return "관련 자료 없음."
        context_parts = []
        for i, (doc, score) in enumerate(search_results, 1):
            source = doc.metadata.get("source", "출처 미상")
            title = doc.metadata.get("title", "제목 없음")
            content = doc.page_content
            context_parts.append(f"[{i}] {title} | {content} (출처: {source})")
        return "\n".join(context_parts)
    
    def _format_profile(self, profile: Union[Dict, object]) -> str:
        parts = ["[사용자 정보]"]
        if isinstance(profile, dict):
            if "age" in profile: parts.append(f"나이: {profile['age']}")
            if "goal" in profile: parts.append(f"목표: {profile['goal']}")
            if "diseases" in profile: parts.append(f"질환: {profile['diseases']}")
            if "allergies" in profile: parts.append(f"알러지: {profile['allergies']}")
        else:
            if hasattr(profile, 'age'): parts.append(f"나이: {profile.age}")
            if hasattr(profile, 'goal'): parts.append(f"목표: {profile.goal}")
        return "\n".join(parts)
    
    def _calculate_confidence(self, search_results: List) -> float:
        if not search_results: return 0.0
        scores = [score for doc, score in search_results[:3]]
        return sum(scores) / len(scores) if scores else 0.0
"""
RAG 체인 - LLM과 지식베이스 연동 (하이브리드 검색 + 시퀀스 추천 + 칼로리 계산 + 대화 메모리 + 다양성 확보)
"""
import time
import random  # ★ [추가] 랜덤 셔플링을 위해 필요
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Optional, Union

# 상대 경로 import 유지
from .knowledge_base import KnowledgeBase
from ..config import GOOGLE_API_KEY

class FitLifeRAG:
    """FitLife AI RAG 시스템"""
    
    def __init__(self):
        self.kb = KnowledgeBase()
        
        # 사용자가 성공한 Gemini 2.5 모델 유지
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=GOOGLE_API_KEY,
            temperature=0.4, # ★ [수정] 창의성을 위해 0.3 -> 0.4로 약간 높임
            max_output_tokens=4096
        )

    def query(
        self, 
        user_query: str, 
        user_profile: Optional[Union[Dict, object]] = None,
        search_categories: Optional[List[str]] = None,
        mode: str = "general",
        chat_history: List = []  # 대화 기록 받기
    ) -> Dict:
        """
        사용자 질문에 대한 RAG 기반 응답 생성 (하이브리드 검색 + 메모리 사용 + 결과 셔플링)
        """
        
        # 1. [검색어 확장] 사용자 의도 및 프로필 정보를 섞어 검색어 보강 (벡터 다양성 확보)
        enhanced_query = user_query
        target_goal = ""
        target_calories = 2000 # 기본값
        
        # 프로필 정보 추출 및 검색어 믹싱
        context_keywords = [] # ★ [추가] 검색어에 섞을 키워드
        
        if isinstance(user_profile, dict): 
            target_goal = user_profile.get("goal", "")
            if user_profile.get("diseases"): context_keywords.append(str(user_profile["diseases"]))
            if user_profile.get("notes"): context_keywords.append(str(user_profile["notes"]))
            
            if "recommended_calories" in user_profile:
                target_calories = int(user_profile["recommended_calories"])
            else:
                target_calories = int(user_profile.get("calories", 2000))
                
        elif user_profile: # 객체인 경우
            if hasattr(user_profile, "goal"): 
                target_goal = user_profile.goal
            
            if hasattr(user_profile, "diseases") and user_profile.diseases: 
                context_keywords.append(str(user_profile.diseases))
            if hasattr(user_profile, "notes") and user_profile.notes: 
                context_keywords.append(str(user_profile.notes))

            if hasattr(user_profile, "recommended_calories") and user_profile.recommended_calories:
                target_calories = int(user_profile.recommended_calories)
            elif hasattr(user_profile, "calories"):
                target_calories = int(user_profile.calories)
        
        # ★ [수정] 프로필 키워드를 검색어에 은근히 섞음 (벡터값 변화 유도)
        context_str = " ".join(context_keywords)
        enhanced_query = f"{user_query} {context_str} {target_goal}"

        if mode == "food":
            enhanced_query += " 영양성분 효능 레시피 식단 추천"
        elif mode == "exercise":
            enhanced_query += " 운동방법 자세 주의사항 효과 루틴"

        # 2. [데이터 확보] 하이브리드 검색 실행 (Top-K를 3배수로 늘려서 다양성 풀 확보)
        search_results_raw = []
        pool_size = 30 # ★ [수정] 15~20개 대신 30개를 가져와서 섞을 예정

        if search_categories:
            for category in search_categories:
                # 카테고리별로 충분히 가져와서 섞음
                results = self.kb.search(enhanced_query, top_k=pool_size, category=category)
                search_results_raw.extend(results)
        else:
            search_results_raw = self.kb.search(enhanced_query, top_k=pool_size)
        
        # 3. [컨텍스트 구성] 셔플링 & 샘플링 전략 적용
        # 중복 제거 및 점수순 정렬
        # (딕셔너리 등을 이용해 중복 문서가 있다면 제거하는 로직이 필요하다면 추가, 여기선 생략)
        search_results_raw.sort(key=lambda x: x[1], reverse=True)
        
        final_results = []
        target_count = 10 # LLM에게 줄 최종 문서 개수

        if len(search_results_raw) >= target_count:
            # ★ [핵심 기능] MMR 유사 방식: 상위권은 유지하되 나머지는 랜덤 섞기
            # (A) Top Tier: 정확도가 가장 높은 상위 3개는 무조건 포함 (할루시네이션 방지)
            top_tier = search_results_raw[:3]
            
            # (B) Random Tier: 나머지 문서들 중에서 랜덤으로 7개 뽑기 (다양성 확보)
            remaining_pool = search_results_raw[3:]
            random_tier = random.sample(remaining_pool, k=min(target_count - 3, len(remaining_pool)))
            
            # 합치고 다시 점수순 정렬 (LLM이 읽기 편하게)
            final_results = top_tier + random_tier
            final_results.sort(key=lambda x: x[1], reverse=True)
        else:
            final_results = search_results_raw

        context = self._build_context(final_results)
        profile_info = self._format_profile(user_profile) if user_profile else ""
        
        # 4. [XAI 프롬프트] 모드별 구조화된 프롬프트 생성
        system_prompt, base_user_message = self._create_xai_prompt(mode, profile_info, user_query, context, target_calories)
        
        # 대화 맥락(History) 주입
        history_text = ""
        if chat_history:
            history_text = "\n[이전 대화 내역 (참고용)]:\n"
            for msg in chat_history[-6:]: 
                role = "사용자" if msg["role"] == "user" else "AI"
                content = str(msg.get("content", ""))
                if len(content) < 500:
                    history_text += f"- {role}: {content}\n"
        
        final_user_message = f"{base_user_message}\n{history_text}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=final_user_message)
        ]
        
        # 5. LLM 호출 (재시도 로직 포함)
        response_content = ""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                response_content = response.content
                break 
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    response_content = "⚠️ 일시적인 AI 서비스 오류입니다. 잠시 후 다시 시도해주세요."
        
        # 6. 결과 반환 포맷팅
        formatted_sources = []
        for doc, score in final_results:
            source_item = doc.metadata.copy()
            source_item['content'] = doc.page_content
            source_item['score'] = score
            formatted_sources.append(source_item)

        return {
            "answer": response_content,
            "sources": formatted_sources,
            "confidence": self._calculate_confidence(final_results)
        }
    
    def _create_xai_prompt(self, mode, profile_info, query, context, target_calories=2000):
        """
        ★ [핵심 업데이트] 칼로리 계산 강제, 운동 시퀀스, 그리고 '다양성' 지시 추가
        """
        
        # 목표 칼로리 범위 설정 (±10%)
        min_cal = int(target_calories * 0.9)
        max_cal = int(target_calories * 1.1)
        per_meal_cal = int(target_calories / 3)

        base_instruction = f"""
        [공통 지침]
        1. [참고 자료]에 기반하여 답변하되, 자료에 없는 내용은 일반적인 의학/건강 상식으로 보완하세요.
        2. 출처가 확실한 정보는 (출처: 국민체력100)과 같이 표기하세요.
        3. 사용자의 건강 상태(질환, 알러지)를 최우선으로 고려하여 경고 사항을 포함하세요.
        4. 이전 대화 내역이 있다면 문맥을 고려하여 자연스럽게 이어가세요.
        5. ★ 중요: 매번 똑같은 답변을 하지 마세요. 제공된 [참고 자료] 목록에서 이전과 다른 메뉴나 운동 조합을 시도하여 다양성을 제공하세요.
        """

        if mode == "food":
            system_prompt = f"""당신은 '임상 영양 전문 AI'입니다.
            단순한 메뉴 추천이 아니라, **철저한 칼로리 계산**을 통해 목표 열량을 맞춰야 합니다.
            
            [매우 중요: 칼로리 계산 지침]
            1. 사용자의 목표 일일 칼로리는 **{target_calories}kcal**입니다.
            2. 추천 식단의 총합이 반드시 **{min_cal}kcal ~ {max_cal}kcal** 사이가 되도록 하세요.
            3. 데이터베이스의 음식 양(예: 100g)으로 칼로리가 부족하다면, **양(g)이나 개수를 배로 늘리세요.** (예: 닭가슴살 100g -> 200g)
            4. 각 끼니(아침/점심/저녁)는 대략 **{per_meal_cal}kcal** 내외로 구성하세요.

            [필수 출력 구조]
            1. 📊 **식단 설계 전략**: 
               - "목표 {target_calories}kcal 달성을 위해 탄수화물 비중을 높이고, 식사량을 평소의 1.5배로 설정했습니다."
            2. 🍽️ **맞춤 식단표 (총 {target_calories}kcal 목표)**: 
               - **아침**: 메뉴명 (약 000kcal) - 재료 및 정확한 분량(g)
               - **점심**: 메뉴명 (약 000kcal) - 재료 및 정확한 분량(g)
               - **저녁**: 메뉴명 (약 000kcal) - 재료 및 정확한 분량(g)
               - **간식**: 메뉴명 (약 000kcal)
            3. 💡 **영양-운동 상호작용 분석 (XAI)**: 
               - **선정 이유**: "사용자가 고강도 운동을 했으므로 근회복을 위해 류신이 풍부한 OO을 선택했습니다." 와 같이 인과관계를 설명.
               - **기대 효과**: 해당 식재료가 목표 달성에 어떻게 기여하는지 설명.
            
            {base_instruction}
            """
        elif mode == "exercise":
            system_prompt = f"""당신은 '전문 스포츠 의학 트레이너 AI'입니다.
            운동은 하나만 추천하는 것이 아니라, **체계적인 루틴(Routine Sequence)**으로 구성해야 합니다.
            
            [필수 출력 구조]
            1. 📊 **운동 처방 분석**: 사용자 목표 및 컨디션에 따른 운동 방향성
            2. 💪 **오늘의 운동 시퀀스**:
               - **Phase 1 [준비 운동]**: 체온 상승 및 관절 가동범위 확보 (5~10분)
               - **Phase 2 [본 운동]**: 주요 근력/유산소 운동 (종목, 세트, 횟수, 휴식시간 명시)
               - **Phase 3 [정리 운동]**: 심박수 안정 및 스트레칭
            3. 💡 **운동 효과 분석 (XAI)**:
               - **타겟 부위**: 자극되는 정확한 근육 명칭
               - **선정 이유**: 사용자의 질환(예: 관절염)이나 목표에 이 루틴이 적합한 이유 설명
            
            {base_instruction}
            """
        else:
            system_prompt = f"당신은 FitLife AI 헬스 코치입니다. 사용자의 질문에 친절하고 전문적으로 답변하세요. {base_instruction}"

        user_message = f"{profile_info}\n[목표 칼로리]: {target_calories}kcal\n[질문]: {query}\n[참고 자료]:\n{context}"
        return system_prompt, user_message

    def _build_context(self, search_results: List) -> str:
        if not search_results: return "관련 자료 없음."
        context_parts = []
        for i, (doc, score) in enumerate(search_results, 1):
            source = doc.metadata.get("source", "출처 미상")
            title = doc.metadata.get("title", "제목 없음")
            content = doc.page_content
            # 하이브리드 검색 점수 표기 (디버깅용)
            context_parts.append(f"[{i}] {title} (유사도: {score:.2f}) | {content}")
        return "\n".join(context_parts)
    
    def _format_profile(self, profile: Union[Dict, object]) -> str:
        # 프로필 포맷팅
        parts = ["[사용자 프로필]"]
        
        if isinstance(profile, dict):
            for k, v in profile.items():
                if v: parts.append(f"- {k}: {v}")
        else:
            # 객체(UserProfile)인 경우
            try:
                if hasattr(profile, 'age'): parts.append(f"- 나이: {profile.age}")
                if hasattr(profile, 'gender'): parts.append(f"- 성별: {profile.gender}")
                if hasattr(profile, 'goal'): parts.append(f"- 목표: {profile.goal}")
                
                # 질환 및 알러지 (리스트라면 보기 좋게 쉼표로 연결)
                if hasattr(profile, 'diseases') and profile.diseases:
                    val = profile.diseases
                    if isinstance(val, list): val = ", ".join(val)
                    parts.append(f"- 질환: {val}")
                
                if hasattr(profile, 'allergies') and profile.allergies:
                    val = profile.allergies
                    if isinstance(val, list): val = ", ".join(val)
                    parts.append(f"- 알러지: {val}")
                
                # ★ 칼로리 표시 로직 (권장 칼로리 우선)
                display_cal = 2000
                if hasattr(profile, 'recommended_calories') and profile.recommended_calories:
                    display_cal = int(profile.recommended_calories)
                elif hasattr(profile, 'calories'):
                    display_cal = int(profile.calories)
                
                parts.append(f"- 목표/권장 칼로리: {display_cal}kcal")

                # ★ 특이사항(notes) 반영
                if hasattr(profile, 'notes') and profile.notes:
                    parts.append(f"- ★ 특이사항(요청): {profile.notes}")

            except:
                pass
                
        return "\n".join(parts)
    
    def _calculate_confidence(self, search_results: List) -> float:
        if not search_results: return 0.0
        # 상위 3개의 평균 유사도를 신뢰도로 사용
        scores = [score for doc, score in search_results[:3]]
        # 1.0을 넘을 수 있는 하이브리드 점수를 정규화
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return min(avg_score, 1.0)
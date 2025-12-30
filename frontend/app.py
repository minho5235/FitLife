"""
FitLife AI - Streamlit 프론트엔드
"""
import streamlit as st
import requests
import json
from typing import Optional

# 페이지 설정
st.set_page_config(
    page_title="FitLife AI",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API URL
API_URL = "http://localhost:8000"

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "profile" not in st.session_state:
    st.session_state.profile = {}
if "health_data" not in st.session_state:
    st.session_state.health_data = {}


def main():
    # 헤더
    st.title("🏃 FitLife AI")
    st.markdown("**AI 기반 건강 상태 분석 및 맞춤 식단/운동 추천 시스템**")
    st.divider()
    
    # 사이드바 - 프로필 설정
    with st.sidebar:
        st.header("👤 내 프로필")
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("나이", min_value=1, max_value=120, value=30)
            height = st.number_input("키 (cm)", min_value=100, max_value=250, value=170)
        with col2:
            gender = st.selectbox("성별", ["남성", "여성"])
            weight = st.number_input("체중 (kg)", min_value=30, max_value=300, value=70)
        
        goal = st.selectbox(
            "건강 목표",
            ["다이어트", "근육증가", "체력향상", "건강유지", "피로회복"]
        )
        
        activity_level = st.select_slider(
            "활동량",
            options=["매우 낮음", "낮음", "보통", "높음", "매우 높음"],
            value="보통"
        )
        
        # 프로필 저장
        st.session_state.profile = {
            "age": age,
            "gender": gender,
            "height": height,
            "weight": weight,
            "goal": goal,
            "activity_level": activity_level
        }
        
        st.divider()
        
        # 건강 데이터 입력
        st.header("📊 오늘의 건강 데이터")
        
        with st.expander("영양 섭취", expanded=False):
            protein = st.slider("단백질 (g)", 0, 200, 60)
            carbs = st.slider("탄수화물 (g)", 0, 500, 250)
            fat = st.slider("지방 (g)", 0, 200, 60)
            calories = st.slider("칼로리 (kcal)", 0, 4000, 2000)
        
        with st.expander("생활 습관", expanded=False):
            sleep = st.slider("수면 시간", 0, 12, 7)
            exercise = st.slider("주당 운동 횟수", 0, 7, 2)
            stress = st.slider("스트레스 수준 (1-10)", 1, 10, 5)
            water = st.slider("물 섭취량 (L)", 0.0, 4.0, 1.5, 0.1)
        
        # 건강 데이터 저장
        st.session_state.health_data = {
            "protein_intake": protein,
            "carb_intake": carbs,
            "fat_intake": fat,
            "calories": calories,
            "sleep_hours": sleep,
            "exercise_days": exercise,
            "stress_level": stress,
            "water_intake": water,
            "height": height,
            "weight": weight
        }
        
        # 건강 분석 버튼
        if st.button("🔍 건강 상태 분석", use_container_width=True):
            analyze_health()
    
    # 메인 영역 - 탭 구성
    tab1, tab2, tab3 = st.tabs(["💬 AI 상담", "📈 건강 분석", "ℹ️ 사용 방법"])
    
    with tab1:
        chat_interface()
    
    with tab2:
        health_analysis_view()
    
    with tab3:
        show_help()


def chat_interface():
    """AI 채팅 인터페이스"""
    st.subheader("💬 AI 건강 상담")
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 참고 자료"):
                    for src in message["sources"][:3]:
                        st.caption(f"- {src.get('metadata', {}).get('source', '출처 미상')} (유사도: {src.get('score', 0):.2f})")
    
    # 채팅 입력
    if prompt := st.chat_input("건강에 대해 무엇이든 물어보세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = call_chat_api(prompt)
                
                if response:
                    st.markdown(response["answer"])
                    
                    # 신뢰도 표시
                    confidence = response.get("confidence", 0)
                    st.caption(f"신뢰도: {confidence*100:.0f}%")
                    
                    # 참고 자료
                    if response.get("sources"):
                        with st.expander("📚 참고 자료"):
                            for src in response["sources"][:3]:
                                st.caption(f"- {src.get('metadata', {}).get('source', '출처 미상')}")
                    
                    # 응답 저장
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response.get("sources", [])
                    })
                else:
                    st.error("응답을 받지 못했습니다. API 서버를 확인해주세요.")


def call_chat_api(message: str) -> Optional[dict]:
    """채팅 API 호출"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "profile": st.session_state.profile,
                "health_data": st.session_state.health_data
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        st.error(f"오류: {e}")
    return None


def analyze_health():
    """건강 분석 API 호출"""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json=st.session_state.health_data,
            timeout=30
        )
        if response.status_code == 200:
            st.session_state.analysis_result = response.json()
            st.success("건강 분석 완료! '건강 분석' 탭을 확인하세요.")
    except requests.exceptions.ConnectionError:
        st.error("⚠️ API 서버에 연결할 수 없습니다.")
    except Exception as e:
        st.error(f"오류: {e}")


def health_analysis_view():
    """건강 분석 결과 표시"""
    st.subheader("📈 건강 상태 분석")
    
    if "analysis_result" not in st.session_state:
        st.info("👈 사이드바에서 건강 데이터를 입력하고 '건강 상태 분석' 버튼을 클릭하세요.")
        return
    
    result = st.session_state.analysis_result
    analysis = result.get("analysis", {})
    
    # 건강 점수
    col1, col2, col3 = st.columns(3)
    with col1:
        score = analysis.get("health_score", 0)
        st.metric("건강 점수", f"{score}점", delta=None)
    with col2:
        status = analysis.get("status", "분석 중")
        st.metric("상태", status)
    with col3:
        issues_count = len(analysis.get("issues", []))
        st.metric("개선 필요 항목", f"{issues_count}개")
    
    st.divider()
    
    # 영향 요인 분석
    st.markdown("### 📊 영향 요인 분석")
    contributions = analysis.get("contributions", [])
    
    if contributions:
        for contrib in contributions:
            impact = contrib.get("impact", 0) * 100
            color = "🔴" if impact > 20 else "🟡" if impact > 10 else "🟢"
            st.markdown(f"{color} **{contrib.get('factor')}**: {contrib.get('value')} (영향도: {impact:.0f}%)")
            st.progress(min(impact / 50, 1.0))
    
    st.divider()
    
    # 추천 사항
    st.markdown("### 💡 추천 사항")
    recommendations = analysis.get("recommendations", [])
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
    else:
        st.success("현재 건강 상태가 양호합니다! 👍")


def show_help():
    """사용 방법 안내"""
    st.subheader("ℹ️ FitLife AI 사용 방법")
    
    st.markdown("""
    ### 1. 프로필 설정
    - 사이드바에서 나이, 성별, 키, 체중 등 기본 정보를 입력하세요.
    - 건강 목표(다이어트, 근육증가 등)를 선택하세요.
    
    ### 2. 건강 데이터 입력
    - 오늘의 영양 섭취량과 생활 습관을 입력하세요.
    - 더 정확한 분석을 위해 가능한 자세히 입력해주세요.
    
    ### 3. AI 상담
    - 채팅창에 건강 관련 질문을 입력하세요.
    - AI가 지식베이스를 검색하고 맞춤 답변을 제공합니다.
    - 참고 자료와 신뢰도도 함께 확인할 수 있습니다.
    
    ### 4. 건강 분석
    - '건강 상태 분석' 버튼을 클릭하면 XAI 분석 결과를 확인할 수 있습니다.
    - 어떤 요인이 건강에 영향을 미치는지, 개선 방법은 무엇인지 확인하세요.
    
    ---
    
    ### ⚠️ 주의사항
    - FitLife AI는 건강 관리 조언을 제공하며, 의료적 진단을 대체하지 않습니다.
    - 심각한 증상이 있으면 반드시 전문의와 상담하세요.
    """)


if __name__ == "__main__":
    main()

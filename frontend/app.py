"""FitLife AI 2.0 - 강화된 웹앱 (XAI 차트 + 비동기 비전 + 상호작용 추천 + 메모리 & 스트리밍)"""
import streamlit as st
import sys
from pathlib import Path
import psycopg2
import os
import asyncio
import pandas as pd
import plotly.express as px
import time # 스트리밍 효과용

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 모듈 임포트
from src.rag.chain import FitLifeRAG
from src.xai.explainer import HealthExplainer
from src.models.user_profile import UserProfile
from src.vision.image_analyzer import ImageAnalyzer
from src.auth.manager import UserManager

st.set_page_config(page_title="FitLife AI 2.0", page_icon="🏃", layout="wide")

# ===== 세션 상태 초기화 =====
if "messages" not in st.session_state: st.session_state.messages = []
if "rag" not in st.session_state: st.session_state.rag = None
if "xai" not in st.session_state: st.session_state.xai = HealthExplainer()
if "analyzer" not in st.session_state: st.session_state.analyzer = None

# 인증 관리자 초기화
if "user_manager" not in st.session_state:
    st.session_state.user_manager = UserManager()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ===== 헬퍼 함수 =====
def init_rag():
    if st.session_state.rag is None:
        with st.spinner("🔄 AI 지식베이스 로딩 중..."):
            st.session_state.rag = FitLifeRAG()

def init_analyzer():
    if st.session_state.analyzer is None:
        with st.spinner("🔄 비전 AI 모델 로딩 중..."):
            st.session_state.analyzer = ImageAnalyzer()

def create_profile() -> UserProfile:
    # 사이드바 입력값(session_state)을 기반으로 프로필 객체 생성
    return UserProfile(
        age=st.session_state.get("age", 30),
        gender=st.session_state.get("gender", "남성"),
        height=st.session_state.get("height", 170.0),
        weight=st.session_state.get("weight", 70.0),
        diseases=st.session_state.get("diseases", []),
        allergies=st.session_state.get("allergies", []),
        goal=st.session_state.get("goal", "건강유지"),
        activity_level=st.session_state.get("activity_level", "보통"),
        sleep_hours=st.session_state.get("sleep_hours", 7.0),
        stress_level=st.session_state.get("stress_level", 5),
        calories=st.session_state.get("calories", 2000),
        protein=st.session_state.get("protein", 60.0)
    )

# ===== 메인 함수 =====
def main():
    # ---------------------------------------------------------
    # 1. 로그인 전 화면 (로그인/회원가입)
    # ---------------------------------------------------------
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🏃 FitLife AI 로그인")
            st.info("개인 맞춤형 건강 관리를 위해 로그인이 필요합니다.")
            
            tab1, tab2 = st.tabs(["로그인", "회원가입"])
            
            with tab1:
                username = st.text_input("아이디", key="login_id")
                password = st.text_input("비밀번호", type="password", key="login_pw")
                # [수정] use_container_width -> width="stretch"
                if st.button("로그인", type="primary", width="stretch"):
                    user = st.session_state.user_manager.login(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.success(f"환영합니다, {user['name']}님!")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

            with tab2:
                st.subheader("새 계정 만들기")
                new_user = st.text_input("새 아이디", key="reg_id")
                new_pw = st.text_input("새 비밀번호", type="password", key="reg_pw")
                new_name = st.text_input("이름", key="reg_name")
                
                # [수정] use_container_width -> width="stretch"
                if st.button("가입하기", width="stretch"):
                    if new_user and new_pw and new_name:
                        success = st.session_state.user_manager.register(
                            new_user, new_pw, new_name, 30, "남성", 170, 70
                        )
                        if success:
                            st.success("가입 성공! 로그인 탭에서 로그인해주세요.")
                        else:
                            st.error("이미 존재하는 아이디입니다.")
                    else:
                        st.warning("모든 정보를 입력해주세요.")
        return  # 로그인 안된 상태면 여기서 종료

    # ---------------------------------------------------------
    # 2. 로그인 후 메인 화면
    # ---------------------------------------------------------
    
    user = st.session_state.current_user
    
    # ===== 사이드바 (DB 정보 연동) =====
    with st.sidebar:
        col_title, col_logout = st.columns([0.7, 0.3])
        with col_title:
            st.title(f"👤 {user['name']}님")
        with col_logout:
            if st.button("로그아웃"):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.rerun()
        
        st.divider()
        
        with st.expander("📋 기본 정보", expanded=True):
            col1, col2 = st.columns(2)
            with col1: 
                st.number_input("나이", 10, 100, value=int(user.get('age', 30)), key="age")
            with col2: 
                g_idx = 0 if user.get('gender') == "남성" else 1
                st.selectbox("성별", ["남성", "여성"], index=g_idx, key="gender")
            
            col3, col4 = st.columns(2)
            with col3: 
                st.number_input("키(cm)", 100.0, 220.0, value=float(user.get('height', 170)), key="height")
            with col4: 
                st.number_input("체중(kg)", 30.0, 200.0, value=float(user.get('weight', 70)), key="weight")
            
            profile = create_profile()
            bmi_color = "green" if profile.bmi_status == "정상" else "orange" if profile.bmi_status in ["과체중", "저체중"] else "red"
            st.markdown(f"**BMI: :{bmi_color}[{profile.bmi}]** ({profile.bmi_status})")
        
        with st.expander("🏥 건강 상태"):
            all_diseases = ["당뇨", "고혈압", "고지혈증", "위염", "관절염", "신장질환", "통풍"]
            all_allergies = ["견과류", "갑각류", "유제품", "글루텐", "계란", "대두", "생선"]

            user_diseases = user.get('diseases', [])
            if isinstance(user_diseases, str): user_diseases = user_diseases.split(',')
            
            user_allergies = user.get('allergies', [])
            if isinstance(user_allergies, str): user_allergies = user_allergies.split(',')

            st.multiselect("질환", all_diseases, default=[d for d in user_diseases if d in all_diseases], key="diseases")
            st.multiselect("알러지", all_allergies, default=[a for a in user_allergies if a in all_allergies], key="allergies")
        
        with st.expander("🎯 목표 & 활동"):
            st.selectbox("건강 목표", ["건강유지", "체중감량", "근육증가", "체력향상", "스트레스해소"], key="goal")
            activity_val = st.slider("활동량 레벨", 1, 5, 3)
            st.session_state.activity_level = {1:"비활동적", 2:"가벼움", 3:"보통", 4:"활발함", 5:"매우활발함"}[activity_val]
        
        with st.expander("📊 오늘의 기록"):
            st.number_input("섭취 칼로리(kcal)", 0, 5000, 2000, key="calories")
            st.number_input("단백질 섭취(g)", 0.0, 300.0, 60.0, key="protein")
            st.number_input("수면 시간(h)", 0.0, 24.0, 7.0, key="sleep_hours")
            st.slider("오늘의 스트레스", 1, 10, 5, key="stress_level")
        
        profile = create_profile()
        st.info(f"💡 권장 칼로리: **{profile.recommended_calories}kcal**")
        
        # [수정] use_container_width -> width="stretch"
        if st.button("💾 정보 수정 저장", width="stretch"):
            try:
                conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                conn.autocommit = True
                cur = conn.cursor()

                diseases_str = ",".join(st.session_state.diseases)
                allergies_str = ",".join(st.session_state.allergies)

                update_query = """
                UPDATE users 
                SET age = %s, gender = %s, height = %s, weight = %s, diseases = %s, allergies = %s
                WHERE username = %s;
                """
                cur.execute(update_query, (
                    st.session_state.age, st.session_state.gender, st.session_state.height,
                    st.session_state.weight, diseases_str, allergies_str, user['username']
                ))

                st.success("✅ 저장 완료!")
                user['age'] = st.session_state.age
                user['gender'] = st.session_state.gender
                user['height'] = st.session_state.height
                user['weight'] = st.session_state.weight
                user['diseases'] = st.session_state.diseases
                user['allergies'] = st.session_state.allergies
                
                cur.close()
                conn.close()
            except Exception as e:
                st.error(f"저장 실패: {e}")

    # ===== 메인 컨텐츠 =====
    st.title("🏃 FitLife AI 2.0")
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 AI 상담", "📸 비전 분석", "📊 건강 XAI", "🍽️ 맞춤 추천", "📖 가이드"
    ])

    # ===== 탭1: AI 상담 (기본 RAG + 스트리밍 + 메모리) =====
    with tab1:
        st.header("💬 무엇이든 물어보세요")
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        if prompt := st.chat_input("예: 당뇨에 좋은 운동 알려줘"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                with st.spinner("🧠 지식베이스 검색 및 생각 중..."):
                    init_rag()
                    result = st.session_state.rag.query(
                        prompt, 
                        create_profile(), 
                        mode="general",
                        chat_history=st.session_state.messages[:-1] 
                    )
                    
                    answer_text = result.get("answer", "죄송합니다. 답변을 생성할 수 없습니다.")
                    
                    for chunk in answer_text.split(" "):
                        full_response += chunk + " "
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.02)
                    
                    message_placeholder.markdown(full_response)
                    
                    if result.get("sources"):
                        with st.expander("📚 근거 자료 (Reference)"):
                            for src in result["sources"][:3]:
                                st.caption(f"- {src.get('title')} ({src.get('source')})")
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    # ===== 탭2: 이미지 분석 (업그레이드: Async + XAI) =====
    with tab2:
        st.header("📸 AI 비전 분석")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥦 식재료 & 식단")
            food_image = st.file_uploader("음식/재료 사진 업로드", type=["jpg", "png"], key="food_img")
            
            if food_image:
                # [수정] use_container_width -> width="stretch"
                st.image(food_image, width="stretch", caption="업로드된 이미지")
                if st.button("🔍 식단 분석 시작", type="primary"):
                    with st.spinner("💎 Gemini 2.5가 분석 중입니다..."):
                        init_analyzer()
                        analysis = asyncio.run(st.session_state.analyzer.analyze_image(food_image.getvalue(), mode="food"))
                        
                        if analysis.get("is_valid"):
                            st.success(f"**{analysis.get('food_name')}** 감지됨!")
                            nutri = analysis.get('macronutrients', {})
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("칼로리", f"{analysis.get('calories')}kcal")
                            c2.metric("단백질", f"{nutri.get('protein')}g")
                            c3.metric("탄수화물", f"{nutri.get('carbs')}g")
                            c4.metric("지방", f"{nutri.get('fat')}g")
                            st.info(f"💡 **AI 분석 의견**: {analysis.get('visual_reasoning')}")
                            
                            st.session_state.messages.append({
                                "role": "system", 
                                "content": f"[이미지 분석] 사용자가 {analysis.get('food_name')}을(를) 먹었습니다. 칼로리: {analysis.get('calories')}"
                            })
                        else:
                            st.error("음식 사진이 아닌 것 같습니다. 다시 시도해주세요.")
        
        with col2:
            st.subheader("🏋️ 운동기구 & 헬스장")
            equip_image = st.file_uploader("운동기구 사진 업로드", type=["jpg", "png"], key="ex_img")
            
            if equip_image:
                # [수정] use_container_width -> width="stretch"
                st.image(equip_image, width="stretch")
                if st.button("🔍 운동법 분석 시작", type="primary"):
                    with st.spinner("💎 기구 사용법 분석 중..."):
                        init_analyzer()
                        analysis = asyncio.run(st.session_state.analyzer.analyze_image(equip_image.getvalue(), mode="equipment"))
                        
                        if analysis.get("is_valid"):
                            st.success(f"**{analysis.get('equipment_name')}** 감지됨!")
                            st.markdown(f"""
                            - **추천 운동**: {analysis.get('recommended_exercise')}
                            - **타겟 부위**: {', '.join(analysis.get('target_muscles', []))}
                            - **주의 사항**: {analysis.get('safety_guide')}
                            """)
                            st.info(f"💡 **AI 분석 의견**: {analysis.get('visual_reasoning')}")
                        else:
                            st.error("운동 기구를 인식하지 못했습니다.")

    # ===== 탭3: 건강 분석 (업그레이드: XAI 레이더 차트) =====
    with tab3:
        st.header("📊 내 건강 상태 (XAI)")
        profile = create_profile()
        
        health_data = {
            "protein_intake": profile.protein, 
            "carb_intake": 300, 
            "fat_intake": 65,
            "calories": profile.calories, 
            "sleep_hours": profile.sleep_hours,
            "exercise_days": 3 if profile.activity_level in ["활발함", "매우활발함"] else 1,
            "stress_level": profile.stress_level, 
            "water_intake": 1.5,
            "height": profile.height, 
            "weight": profile.weight
        }
        
        analysis = st.session_state.xai.analyze_health_factors(health_data)
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.subheader("🕸️ 건강 밸런스 차트")
            features = analysis.get('raw_features', {})
            if features:
                df = pd.DataFrame(dict(
                    r=[
                        features.get('단백질_섭취율', 0), 
                        features.get('운동_빈도', 0), 
                        features.get('수면_시간', 0), 
                        1 - max(0, features.get('스트레스_수준', 0.5) - 0.2), 
                        features.get('수분_섭취량', 0)
                    ],
                    theta=['단백질', '운동', '수면', '스트레스 관리', '수분']
                ))
                
                fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0, 1.5])
                fig.update_traces(fill='toself', line_color='#4CAF50')
                fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
                
                # [수정] use_container_width -> width="stretch"
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning("분석 데이터가 부족합니다.")

        with col2:
            st.subheader("📝 종합 분석 결과")
            st.metric("종합 건강 점수", f"{analysis['health_score']}점", delta=analysis['status'])
            
            if analysis["issues"]:
                st.error("⚠️ 주요 개선 필요 사항")
                for issue in analysis["issues"]: st.write(f"- {issue}")
            
            if analysis["recommendations"]:
                st.success("💡 AI 추천 솔루션")
                for rec in analysis["recommendations"]: st.write(f"- {rec}")

    # ===== 탭4: 맞춤 추천 (업그레이드: 상호작용 강화) =====
    with tab4:
        st.header("🍽️ & 💪 맞춤형 가이드")
        profile = create_profile()

        rec_tab1, rec_tab2 = st.tabs(["🥗 식단 추천", "💪 운동 추천"])

        with rec_tab1:
            st.subheader("개인 맞춤 식단")
            st.markdown(f"**{profile.goal}** 목표와 **{profile.allergies}** 알러지를 고려합니다.")
            
            workout_done = st.checkbox("오늘 고강도 운동을 하셨나요?")
            
            # [수정] use_container_width -> width="stretch"
            if st.button("🍽️ 오늘의 식단 생성", type="primary", width="stretch"):
                with st.spinner("레시피 및 영양 정보 검색 중..."):
                    init_rag()
                    context_query = f"{profile.goal} 식단 추천."
                    if workout_done:
                        context_query += " (방금 고강도 운동을 했으니 근육 회복을 위한 고단백, 빠른 탄수화물 보충 식단 위주로)"
                    else:
                        context_query += " (활동량이 적으므로 저칼로리, 고식이섬유 위주로)"

                    result = st.session_state.rag.query(
                        context_query, 
                        user_profile=profile,
                        search_categories=['food'],
                        mode="food"
                    )
                    st.markdown(result.get("answer", ""))
                    
                    if result.get("sources"):
                        with st.expander("데이터 출처 (식품안전나라)"):
                            for source in result["sources"]:
                                st.caption(f"- {source.get('title')}")

        with rec_tab2:
            st.subheader("개인 맞춤 운동 루틴")
            condition = st.select_slider("오늘의 컨디션은?", options=["나쁨", "보통", "좋음", "최상"])
            
            # [수정] use_container_width -> width="stretch"
            if st.button("🏃 오늘의 운동 루틴 생성", type="primary", width="stretch"):
                with st.spinner("운동 루틴 구성 중..."):
                    init_rag()
                    context_query = f"{profile.goal}을 위한 운동 루틴."
                    if condition == "나쁨":
                        context_query += " (컨디션이 안 좋으니 저강도, 스트레칭, 회복 위주로)"
                    elif condition == "최상":
                        context_query += " (컨디션이 최상이므로 고강도 인터벌 혹은 근력 강화 위주로)"
                    
                    result = st.session_state.rag.query(
                        context_query, 
                        user_profile=profile,
                        search_categories=['video'],
                        mode="exercise"
                    )
                    st.markdown(result.get("answer", ""))
                    
                    if result.get("sources"):
                        st.divider()
                        st.markdown("### 📺 추천 운동 영상")
                        for source in result["sources"]:
                            if source.get('video_url'):
                                st.markdown(f"**[{source.get('title')}]({source.get('video_url')})**")

    # ===== 탭5: 사용법 =====
    with tab5:
        st.header("📖 FitLife AI 2.0 가이드")
        st.markdown("""
        ### 🌟 새로워진 기능
        1. **XAI 건강 차트**: '건강 XAI' 탭에서 내 건강 밸런스를 육각형 차트로 확인하세요.
        2. **스마트 비전**: 음식이나 운동기구 사진을 올리면 AI가 즉시 분석해줍니다.
        3. **상호작용 추천**: 운동 여부와 컨디션에 따라 식단과 운동을 유기적으로 추천합니다.
        
        ### 🛠️ 데이터베이스 연동
        - **PostgreSQL**: 회원 정보와 프로필이 안전하게 저장됩니다.
        - **ChromaDB**: 국민체력100 및 식품안전나라 데이터가 벡터로 저장되어 검색됩니다.
        """)
    
    st.divider()
    st.caption("Designed by FitLife Team | Powered by Gemini 2.5 & Streamlit")

if __name__ == "__main__":
    main()
"""
FitLife AI 2.0 - 통합 웹 애플리케이션
(로그인 + RAG 채팅 + 비전 분석(식재료/운동기구) + XAI 건강 분석 + DB 연동)
"""
import streamlit as st
import sys
import os
import asyncio
import pandas as pd
import plotly.express as px
import time
import psycopg2
from pathlib import Path
from PIL import Image

# --------------------------------------------------------------------------
# 1. 환경 설정 및 모듈 경로 잡기
# --------------------------------------------------------------------------
# 현재 파일(app.py)의 상위 상위 폴더(프로젝트 루트)를 path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from dotenv import load_dotenv
load_dotenv()

# 사용자 정의 모듈 임포트
# (파일 경로가 src/rag/chain.py, src/vision/analysis.py 등에 있어야 함)
try:
    from src.rag.chain import FitLifeRAG
    from src.xai.explainer import HealthExplainer
    from src.models.user_profile import UserProfile
    from src.vision.image_analyzer import ImageAnalyzer  # v2.2 (analysis.py)
    from src.auth.manager import UserManager
except ImportError as e:
    st.error(f"모듈 임포트 오류: {e}")
    st.stop()

# 페이지 기본 설정
st.set_page_config(
    page_title="FitLife AI 2.0", 
    page_icon="🏃", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------------------------------
# 2. 세션 상태(Session State) 초기화
# --------------------------------------------------------------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "rag" not in st.session_state: st.session_state.rag = None
if "xai" not in st.session_state: st.session_state.xai = HealthExplainer()
if "analyzer" not in st.session_state: st.session_state.analyzer = None  # 비전 분석기

# 인증 관련 상태
if "user_manager" not in st.session_state: st.session_state.user_manager = UserManager()
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_user" not in st.session_state: st.session_state.current_user = None

# --------------------------------------------------------------------------
# 3. 헬퍼 함수 정의
# --------------------------------------------------------------------------
def init_rag():
    """RAG 시스템 Lazy Loading"""
    if st.session_state.rag is None:
        with st.spinner("🔄 AI 지식베이스(RAG) 로딩 중..."):
            st.session_state.rag = FitLifeRAG()

def init_analyzer():
    """비전 분석기 Lazy Loading"""
    if st.session_state.analyzer is None:
        with st.spinner("🔄 비전 AI(Gemini Vision) 모델 로딩 중..."):
            st.session_state.analyzer = ImageAnalyzer()

def create_profile_object() -> UserProfile:
    """세션 상태의 입력값들을 모아 UserProfile 객체 생성"""
    # Multiselect(리스트)와 Text Input(문자열) 병합 로직
    selected_diseases = st.session_state.get("diseases", [])
    custom_disease = st.session_state.get("custom_disease", "")
    if custom_disease:
        # 쉼표로 구분된 문자열을 리스트로 변환하여 합침
        selected_diseases = selected_diseases + [d.strip() for d in custom_disease.split(",") if d.strip()]

    selected_allergies = st.session_state.get("allergies", [])
    custom_allergy = st.session_state.get("custom_allergy", "")
    if custom_allergy:
        selected_allergies = selected_allergies + [a.strip() for a in custom_allergy.split(",") if a.strip()]

    return UserProfile(
        age=st.session_state.get("age", 30),
        gender=st.session_state.get("gender", "남성"),
        height=st.session_state.get("height", 170.0),
        weight=st.session_state.get("weight", 70.0),
        diseases=selected_diseases,
        allergies=selected_allergies,
        goal=st.session_state.get("goal", "건강유지"),
        activity_level=st.session_state.get("activity_level", "보통"),
        sleep_hours=st.session_state.get("sleep_hours", 7.0),
        stress_level=st.session_state.get("stress_level", 5),
        calories=st.session_state.get("calories", 2000),
        protein=st.session_state.get("protein", 60.0),
        notes=st.session_state.get("notes", "")
    )

# --------------------------------------------------------------------------
# 4. 메인 애플리케이션 로직
# --------------------------------------------------------------------------
def main():
    # ======================================================================
    # [SCENE 1] 로그인 / 회원가입 화면
    # ======================================================================
    if not st.session_state.logged_in:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🏃 FitLife AI 로그인")
            st.info("개인 맞춤형 건강 관리를 위해 로그인이 필요합니다.")
            
            tab_login, tab_signup = st.tabs(["로그인", "회원가입"])
            
            with tab_login:
                username = st.text_input("아이디", key="login_id")
                password = st.text_input("비밀번호", type="password", key="login_pw")
                
                if st.button("로그인", type="primary", use_container_width=True):
                    user = st.session_state.user_manager.login(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user
                        st.success(f"환영합니다, {user['name']}님!")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

            with tab_signup:
                st.subheader("새 계정 만들기")
                new_user = st.text_input("새 아이디", key="reg_id")
                new_pw = st.text_input("새 비밀번호", type="password", key="reg_pw")
                new_name = st.text_input("이름", key="reg_name")
                
                if st.button("가입하기", use_container_width=True):
                    if new_user and new_pw and new_name:
                        # 기본값으로 가입
                        success = st.session_state.user_manager.register(
                            new_user, new_pw, new_name, 30, "남성", 170, 70
                        )
                        if success:
                            st.success("가입 성공! 로그인 탭에서 로그인해주세요.")
                        else:
                            st.error("이미 존재하는 아이디입니다.")
                    else:
                        st.warning("모든 정보를 입력해주세요.")
        return  # 로그인 전에는 아래 코드 실행 안 함

    # ======================================================================
    # [SCENE 2] 로그인 후 메인 화면
    # ======================================================================
    
    user = st.session_state.current_user
    
    # -------------------------- [Sidebar] 프로필 관리 --------------------------
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
        
        # --- 1. 신체 정보 ---
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
            
            # BMI 실시간 계산
            p = create_profile_object()
            bmi_color = "green" if p.bmi_status == "정상" else "orange" if p.bmi_status in ["과체중", "저체중"] else "red"
            st.markdown(f"**BMI: :{bmi_color}[{p.bmi}]** ({p.bmi_status})")
        
        # --- 2. 건강 상태 (질환/알러지) ---
        with st.expander("🏥 건강 상태"):
            all_diseases = ["당뇨", "고혈압", "고지혈증", "위염", "관절염", "신장질환", "통풍"]
            all_allergies = ["견과류", "갑각류", "유제품", "글루텐", "계란", "대두", "생선"]

            # DB 저장된 값 불러오기 (문자열 -> 리스트 변환)
            user_diseases = user.get('diseases', [])
            if isinstance(user_diseases, str): user_diseases = user_diseases.split(',')
            
            user_allergies = user.get('allergies', [])
            if isinstance(user_allergies, str): user_allergies = user_allergies.split(',')
            
            user_notes = user.get('notes', "")

            # 기본 목록에 있는 것 vs 없는 것(Custom) 분리
            default_diseases = [d for d in user_diseases if d in all_diseases]
            default_allergies = [a for a in user_allergies if a in all_allergies]
            
            custom_diseases_init = ",".join([d for d in user_diseases if d not in all_diseases and d.strip()])
            custom_allergies_init = ",".join([a for a in user_allergies if a not in all_allergies and a.strip()])

            st.multiselect("질환 (선택)", all_diseases, default=default_diseases, key="diseases")
            st.text_input("기타 질환 (직접 입력)", value=custom_diseases_init, key="custom_disease")
            
            st.multiselect("알러지 (선택)", all_allergies, default=default_allergies, key="allergies")
            st.text_input("기타 알러지 (직접 입력)", value=custom_allergies_init, key="custom_allergy")
            
            st.markdown("---")
            st.text_area("📝 특이사항 / 요청사항", value=user_notes, height=80, key="notes")

        # --- 3. 목표 및 데일리 데이터 ---
        with st.expander("🎯 목표 & 활동"):
            # 목표 index 찾기
            goals = ["건강유지", "체중감량", "근육증가", "체력향상", "스트레스해소"]
            curr_goal = user.get('goal', "건강유지")
            g_idx = goals.index(curr_goal) if curr_goal in goals else 0
            
            st.selectbox("건강 목표", goals, index=g_idx, key="goal")
            
            activity_val = st.slider("활동량 레벨", 1, 5, 3)
            st.session_state.activity_level = {1:"비활동적", 2:"가벼움", 3:"보통", 4:"활발함", 5:"매우활발함"}[activity_val]
        
        with st.expander("📊 오늘의 기록"):
            st.number_input("섭취 칼로리(kcal)", 0, 5000, 2000, key="calories")
            st.number_input("단백질 섭취(g)", 0.0, 300.0, 60.0, key="protein")
            st.number_input("수면 시간(h)", 0.0, 24.0, 7.0, key="sleep_hours")
            st.slider("오늘의 스트레스", 1, 10, 5, key="stress_level")
        
        # 권장 칼로리 표시
        p = create_profile_object()
        st.info(f"💡 권장 칼로리: **{p.recommended_calories}kcal**")
        
        # --- DB 저장 버튼 ---
        if st.button("💾 정보 수정 저장", use_container_width=True):
            try:
                conn = psycopg2.connect(os.getenv("DATABASE_URL"))
                conn.autocommit = True
                cur = conn.cursor()

                # DB 저장을 위해 리스트들을 쉼표 문자열로 변환
                final_diseases = st.session_state.diseases + [x.strip() for x in st.session_state.custom_disease.split(",") if x.strip()]
                final_allergies = st.session_state.allergies + [x.strip() for x in st.session_state.custom_allergy.split(",") if x.strip()]

                diseases_str = ",".join(final_diseases)
                allergies_str = ",".join(final_allergies)
                notes_str = st.session_state.notes

                update_query = """
                UPDATE users 
                SET age = %s, gender = %s, height = %s, weight = %s, 
                    diseases = %s, allergies = %s, notes = %s, goal = %s
                WHERE username = %s;
                """
                cur.execute(update_query, (
                    st.session_state.age, st.session_state.gender, st.session_state.height,
                    st.session_state.weight, diseases_str, allergies_str, notes_str, 
                    st.session_state.goal, user['username']
                ))

                st.success("✅ 저장 완료!")
                # 세션 User 정보 즉시 업데이트 (새로고침 없이 반영)
                user['age'] = st.session_state.age
                user['gender'] = st.session_state.gender
                user['height'] = st.session_state.height
                user['weight'] = st.session_state.weight
                user['diseases'] = final_diseases
                user['allergies'] = final_allergies
                user['notes'] = notes_str
                user['goal'] = st.session_state.goal
                
                cur.close()
                conn.close()
            except Exception as e:
                st.error(f"저장 실패: {e}")

    # -------------------------- [Main] 탭 구성 --------------------------
    st.title("🏃 FitLife AI 2.0")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 AI 상담", "📸 비전 분석", "📊 건강 XAI", "🍽️ 맞춤 추천", "📖 가이드"
    ])

    # ===== [TAB 1] AI 상담 (RAG) =====
    with tab1:
        st.header("💬 무엇이든 물어보세요")
        
        # 대화 기록 표시
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # 채팅 입력
        if prompt := st.chat_input("예: 당뇨에 좋은 운동 알려줘"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                with st.spinner("🧠 지식베이스 검색 및 생각 중..."):
                    init_rag() # RAG 로드
                    result = st.session_state.rag.query(
                        prompt, 
                        user_profile=create_profile_object(), 
                        mode="general",
                        chat_history=st.session_state.messages[:-1] 
                    )
                    
                    answer_text = result.get("answer", "죄송합니다. 답변을 생성할 수 없습니다.")
                    
                    # 스트리밍 효과
                    for chunk in answer_text.split(" "):
                        full_response += chunk + " "
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.02)
                    
                    message_placeholder.markdown(full_response)
                    
                    # 출처 표시
                    if result.get("sources"):
                        with st.expander("📚 근거 자료 (Reference)"):
                            for src in result["sources"][:3]:
                                st.caption(f"- {src.get('title')} (유사도: {src.get('score', 0):.2f})")
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    # ===== [TAB 2] 비전 분석 (업그레이드: 탭 분리 + 연쇄 작용) =====
    with tab2:
        st.header("📸 AI 비전 분석")
        
        # 탭을 나눠서 UI 구성
        v_tab1, v_tab2 = st.tabs(["🥦 식재료 & 레시피", "🏋️ 운동기구 & 루틴"])
        
        with v_tab1:
            # ★ 사용자가 사진의 성격을 선택하게 함
            analysis_type = st.radio(
                "사진의 종류를 선택해주세요:",
                ["🥗 식재료 (냉장고 파먹기)", "🍔 완성된 음식 (영양 분석)"],
                horizontal=True
            )
            
            if "식재료" in analysis_type:
                st.info("냉장고 속 재료 사진을 올리면 **요리 레시피**를 추천합니다.")
            else:
                st.info("드시는 음식 사진을 올리면 **칼로리와 영양 성분**을 분석해줍니다.")

            food_file = st.file_uploader("음식/재료 사진 업로드", type=["jpg", "png", "jpeg"], key="food_u")
            
            if food_file:
                st.image(food_file, caption="업로드된 사진", width=300)
                
                # 버튼 텍스트도 상황에 맞게 변경
                btn_text = "🔍 재료 분석 및 레시피 추천" if "식재료" in analysis_type else "📊 영양 성분 및 건강 분석"
                
                if st.button(btn_text, key="btn_food", type="primary"):
                    init_analyzer()
                    
                    # 1. 완성된 음식 (영양 분석) 모드
                    if "완성된 음식" in analysis_type:
                        with st.spinner("🍔 음식의 영양소와 건강 영향을 분석 중입니다..."):
                            # 사용자 프로필 정보를 문자열로 만들어서 전달 (당뇨 여부 등 반영)
                            p = create_profile_object()
                            profile_summary = f"질환: {p.diseases}, 목표: {p.goal}, 알러지: {p.allergies}"
                            
                            # mode="meal"로 호출
                            analysis = asyncio.run(st.session_state.analyzer.analyze_image(
                                food_file.getvalue(), 
                                mode="meal", 
                                user_profile=profile_summary
                            ))
                            
                            if analysis.get("success"):
                                st.success(f"**{analysis.get('food_name')}** 분석 완료!")
                                
                                # 영양 성분 표시
                                nutri = analysis.get('nutrients', {})
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("🔥 칼로리", f"{analysis.get('calories')} kcal")
                                col2.metric("🥩 단백질", f"{nutri.get('protein', '0g')}")
                                col3.metric("🍚 탄수화물", f"{nutri.get('carbs', '0g')}")
                                col4.metric("🧂 나트륨", f"{nutri.get('sodium', '0mg')}")

                                st.divider()
                                
                                # 건강 분석 (XAI)
                                st.subheader("🩺 건강 영향 분석")
                                st.warning(f"💡 {analysis.get('health_analysis')}")
                                
                                st.subheader("👨‍⚕️ 섭취 가이드")
                                st.info(analysis.get('eating_guide'))
                                
                                if analysis.get('better_choice'):
                                    st.caption(f"✨ **더 건강한 선택:** {analysis.get('better_choice')}")
                            else:
                                st.error("분석 실패: 음식을 인식하지 못했습니다.")

                    # 2. 식재료 (요리 추천) 모드 (기존 로직)
                    else:
                        with st.spinner("🥦 재료 스캔 및 레시피 구상 중..."):
                            ing_result = asyncio.run(st.session_state.analyzer.analyze_image(food_file.getvalue(), mode="ingredients"))
                            
                            if ing_result.get("success"):
                                ingredients_list = ing_result.get("ingredients", [])
                                detected_names = [ing['name'] for ing in ingredients_list]
                                
                                st.success(f"✅ 발견된 재료: {', '.join(detected_names)}")
                                
                                # 레시피 추천
                                recipe_result = st.session_state.analyzer.suggest_recipes(detected_names)
                                
                                if recipe_result.get("success"):
                                    st.subheader("🍽️ 추천 요리")
                                    for idx, recipe in enumerate(recipe_result.get("recipes", []), 1):
                                        with st.expander(f"#{idx} {recipe['name']}", expanded=True):
                                            st.write(recipe.get('description'))
                                            st.metric("칼로리", f"{recipe.get('nutrition', {}).get('calories')}kcal")
                                else:
                                    st.warning("레시피를 찾지 못했습니다.")
                            else:
                                st.error("재료를 찾지 못했습니다.")

        # --- [Sub Tab 2] 운동기구 분석 ---
        with v_tab2:
            st.info("헬스장 기구 사진을 올리면, 사용법과 추천 루틴을 알려드립니다.")
            gym_file = st.file_uploader("운동기구 사진 업로드", type=["jpg", "png", "jpeg"], key="gym_u")
            
            if gym_file:
                st.image(gym_file, caption="업로드된 사진", width=300)
                
                if st.button("💪 기구 분석 및 루틴 생성", key="btn_gym"):
                    with st.spinner("기구 분석 중..."):
                        init_analyzer()
                        
                        # [Step 1] 기구 분석
                        equip_result = asyncio.run(st.session_state.analyzer.analyze_image(gym_file.getvalue(), mode="equipment"))
                        
                        if equip_result.get("success"):
                            equip_list = equip_result.get("equipment", [])
                            env = equip_result.get("environment", "알 수 없음")
                            equip_names = [e['name'] for e in equip_list]
                            
                            st.divider()
                            st.success(f"📍 장소: {env} / 감지된 기구: {', '.join(equip_names)}")
                            
                            for eq in equip_list:
                                st.write(f"- **{eq['name']}** ({eq.get('category')})")
                            
                            # [Step 2] 루틴 추천
                            with st.spinner("🔥 운동 루틴 생성 중..."):
                                routine_result = st.session_state.analyzer.suggest_exercises(
                                    equipment=equip_names,
                                    target_area="전신",
                                    duration=30
                                )
                            
                            if routine_result.get("success"):
                                st.subheader(f"📋 {routine_result.get('routine_name')}")
                                st.caption(f"예상 소모 칼로리: {routine_result.get('estimated_calories')}kcal")
                                
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.markdown("#### 1. 웜업")
                                    for w in routine_result.get("warmup", []):
                                        st.caption(f"- {w['name']} ({w['duration']})")
                                with c2:
                                    st.markdown("#### 2. 본 운동")
                                    for m in routine_result.get("main_workout", []):
                                        st.markdown(f"**{m['name']}**")
                                        st.caption(f"{m.get('sets')}세트 x {m.get('reps')}")
                                with c3:
                                    st.markdown("#### 3. 쿨다운")
                                    for c in routine_result.get("cooldown", []):
                                        st.caption(f"- {c['name']} ({c['duration']})")
                            else:
                                st.warning("루틴 정보를 가져오지 못했습니다.")
                        else:
                            st.error("기구를 식별하지 못했습니다.")

    # ===== [TAB 3] 건강 XAI (차트) =====
    with tab3:
        st.header("📊 내 건강 상태 (XAI)")
        p = create_profile_object()
        
        # 분석용 데이터 구성
        health_data = {
            "protein_intake": p.protein, 
            "carb_intake": 300, # 예시 값 (실제론 입력 받아야 함)
            "fat_intake": 65,
            "calories": p.calories, 
            "sleep_hours": p.sleep_hours,
            "exercise_days": 3 if p.activity_level in ["활발함", "매우활발함"] else 1,
            "stress_level": p.stress_level, 
            "water_intake": 1.5,
            "height": p.height, 
            "weight": p.weight
        }
        
        analysis = st.session_state.xai.analyze_health_factors(health_data)
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.subheader("🕸️ 건강 밸런스 차트")
            features = analysis.get('raw_features', {})
            if features:
                df_chart = pd.DataFrame(dict(
                    r=[
                        features.get('단백질_섭취율', 0), 
                        features.get('운동_빈도', 0), 
                        features.get('수면_시간', 0), 
                        1 - max(0, features.get('스트레스_수준', 0.5) - 0.2), 
                        features.get('수분_섭취량', 0)
                    ],
                    theta=['단백질', '운동', '수면', '스트레스 관리', '수분']
                ))
                
                fig = px.line_polar(df_chart, r='r', theta='theta', line_close=True, range_r=[0, 1.5])
                fig.update_traces(fill='toself', line_color='#4CAF50')
                fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("분석할 데이터가 부족합니다.")

        with col2:
            st.subheader("📝 종합 분석 결과")
            st.metric("종합 건강 점수", f"{analysis['health_score']}점", delta=analysis['status'])
            
            if analysis["issues"]:
                st.error("⚠️ 주요 개선 필요 사항")
                for issue in analysis["issues"]: st.write(f"- {issue}")
            
            if analysis["recommendations"]:
                st.success("💡 AI 추천 솔루션")
                for rec in analysis["recommendations"]: st.write(f"- {rec}")

    # ===== [TAB 4] 맞춤 추천 (상호작용) =====
    with tab4:
        st.header("🍽️ & 💪 상황별 가이드")
        p = create_profile_object()

        rec_tab1, rec_tab2 = st.tabs(["🥗 식단 추천", "💪 운동 추천"])

        with rec_tab1:
            st.subheader("개인 맞춤 식단")
            workout_done = st.checkbox("오늘 고강도 운동을 하셨나요?")
            
            if st.button("🍽️ 오늘의 식단 생성", type="primary", use_container_width=True):
                with st.spinner("레시피 검색 중..."):
                    init_rag()
                    context_query = f"{p.goal} 식단 추천."
                    if workout_done:
                        context_query += " (방금 고강도 운동을 했으니 근육 회복을 위한 고단백 식단 위주로)"
                    else:
                        context_query += " (활동량이 적으므로 저칼로리, 소화가 잘 되는 식단 위주로)"

                    result = st.session_state.rag.query(
                        context_query, 
                        user_profile=p,
                        search_categories=['food'],
                        mode="food"
                    )
                    st.markdown(result.get("answer", ""))

        with rec_tab2:
            st.subheader("개인 맞춤 운동 루틴")
            condition = st.select_slider("오늘의 컨디션은?", options=["나쁨", "보통", "좋음", "최상"])
            
            if st.button("🏃 오늘의 운동 루틴 생성", type="primary", use_container_width=True):
                with st.spinner("운동 루틴 구성 중..."):
                    init_rag()
                    context_query = f"{p.goal}을 위한 운동 루틴."
                    if condition == "나쁨":
                        context_query += " (컨디션이 안 좋으니 저강도, 스트레칭 위주로)"
                    elif condition == "최상":
                        context_query += " (컨디션 최상, 고강도 인터벌 포함)"
                    
                    result = st.session_state.rag.query(
                        context_query, 
                        user_profile=p,
                        search_categories=['video'],
                        mode="exercise"
                    )
                    st.markdown(result.get("answer", ""))
                    
                    if result.get("sources"):
                        st.markdown("### 📺 관련 영상")
                        for source in result["sources"]:
                            if source.get('video_url'):
                                st.markdown(f"- [{source.get('title')}]({source.get('video_url')})")

    # ===== [TAB 5] 가이드 =====
    with tab5:
        st.header("📖 FitLife AI 2.0 가이드")
        st.markdown("""
        ### 🌟 기능 소개
        1. **AI 상담**: 평소 궁금했던 건강 정보를 물어보세요. (예: "당뇨에 좋은 과일은?")
        2. **비전 분석**:
           - **식재료**: 냉장고 사진을 찍으면 요리를 추천해줍니다.
           - **운동기구**: 헬스장 기구를 찍으면 사용법을 알려줍니다.
        3. **건강 XAI**: 내 생활 습관 점수를 차트로 분석해줍니다.
        """)
    
    st.divider()
    st.caption("Designed by FitLife Team | Powered by Gemini 2.5 & Streamlit")

if __name__ == "__main__":
    main()
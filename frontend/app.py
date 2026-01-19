"""FitLife AI 2.0 - 강화된 웹앱"""
import streamlit as st
import sys
from pathlib import Path
import psycopg2
import os
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
        with st.spinner("🔄 AI 초기화 중..."):
            st.session_state.rag = FitLifeRAG()

def init_analyzer():
    if st.session_state.analyzer is None:
        with st.spinner("🔄 이미지 분석기 초기화 중..."):
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
        st.title("🏃 FitLife AI 로그인")
        st.info("서비스를 이용하려면 로그인이 필요합니다.")
        
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            username = st.text_input("아이디", key="login_id")
            password = st.text_input("비밀번호", type="password", key="login_pw")
            if st.button("로그인", type="primary"):
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
            
            if st.button("가입하기"):
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
                st.number_input("나이", 10, 100, value=user.get('age', 30), key="age")
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
            # ★ [수정됨] 전체 리스트를 제공하여 '생선' 등의 값이 있어도 에러가 나지 않게 함
            all_diseases = ["당뇨", "고혈압", "고지혈증", "위염", "관절염", "신장질환", "통풍"]
            all_allergies = ["견과류", "갑각류", "유제품", "글루텐", "계란", "대두", "생선"]

            st.multiselect("질환", all_diseases, default=user.get('diseases', []), key="diseases")
            st.multiselect("알러지", all_allergies, default=user.get('allergies', []), key="allergies")
        
        with st.expander("🎯 목표"):
            st.selectbox("건강 목표", ["건강유지", "체중감량", "근육증가", "체력향상", "스트레스해소"], key="goal")
            activity_val = st.slider("활동량", 1, 5, 3)
            st.session_state.activity_level = {1:"비활동적", 2:"가벼움", 3:"보통", 4:"활발함", 5:"매우활발함"}[activity_val]
        
        with st.expander("📊 오늘의 데이터"):
            st.number_input("칼로리", 0, 5000, 2000, key="calories")
            st.number_input("단백질(g)", 0.0, 300.0, 60.0, key="protein")
            st.number_input("수면(시간)", 0.0, 24.0, 7.0, key="sleep_hours")
            st.slider("스트레스", 1, 10, 5, key="stress_level")
        
        profile = create_profile()
        st.info(f"💡 권장 칼로리: **{profile.recommended_calories}kcal**")
        
        if st.button("💾 정보 수정 저장"):
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

                st.success("성공적으로 수정되었습니다!")
                
                # 세션 정보 갱신
                st.session_state.current_user['age'] = st.session_state.age
                st.session_state.current_user['gender'] = st.session_state.gender
                st.session_state.current_user['height'] = st.session_state.height
                st.session_state.current_user['weight'] = st.session_state.weight
                st.session_state.current_user['diseases'] = st.session_state.diseases
                st.session_state.current_user['allergies'] = st.session_state.allergies
                
                cur.close()
                conn.close()
            except Exception as e:
                st.error(f"저장 실패: {e}")

    # ===== 메인 컨텐츠 =====
    st.title("🏃 FitLife AI 2.0")
    st.caption("AI 기반 개인 맞춤형 건강 관리 | 📸 이미지 분석 | 🍽️ 식단 추천 | 💪 운동 추천")

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 AI 상담", "📸 이미지 분석", "📊 건강 분석", "🍽️ 맞춤 추천", "📖 사용법"])

    # ===== 탭1: AI 상담 =====
    with tab1:
        st.header("💬 AI 건강 상담")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input("건강에 대해 물어보세요..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("🤔 생각 중..."):
                    init_rag()
                    # 일반 상담은 모든 카테고리에서 검색
                    result = st.session_state.rag.query(prompt, create_profile(), mode="general")
                    response = result.get("answer", "죄송합니다. 답변을 생성할 수 없습니다.")
                    st.markdown(response)
                    
                    if result.get("sources"):
                        with st.expander("📚 참고 자료"):
                            for src in result["sources"][:5]:
                                title = src.get("title", "")
                                source = src.get("source", "")
                                if title: st.caption(f"• {title} ({source})")
            
            st.session_state.messages.append({"role": "assistant", "content": response})

    # ===== 탭2: 이미지 분석 (복구됨) =====
    with tab2:
        st.header("📸 이미지 분석")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥬 식재료 분석")
            food_image = st.file_uploader("식재료 사진", type=["jpg", "jpeg", "png"], key="food_img")
            
            if food_image:
                st.image(food_image, use_container_width=True)
                meal_type = st.selectbox("식사 종류", ["any", "breakfast", "lunch", "dinner", "snack"],
                    format_func=lambda x: {"any": "🍽️ 상관없음", "breakfast": "🌅 아침", "lunch": "☀️ 점심", "dinner": "🌙 저녁", "snack": "🍪 간식"}[x])
                
                if st.button("🔍 식재료 분석", type="primary"):
                    with st.spinner("🔬 분석 중..."):
                        init_analyzer()
                        analysis = st.session_state.analyzer.analyze_ingredients(food_image.getvalue())
                        if analysis.get("success"):
                            st.success("✅ 분석 완료!")
                            st.markdown("### 🥬 인식된 재료")
                            for ing in analysis.get("ingredients", []):
                                st.info(f"**{ing['name']}** - {ing.get('quantity', '')} ({ing.get('category', '')})")
                            
                            profile = create_profile()
                            restrictions = profile.allergies + profile.diseases
                            with st.spinner("🍳 요리 추천 중..."):
                                recipes = st.session_state.analyzer.suggest_recipes([i["name"] for i in analysis.get("ingredients", [])], restrictions, meal_type)
                                if recipes.get("recipes"):
                                    st.markdown("### 🍳 추천 요리")
                                    for recipe in recipes.get("recipes", []):
                                        with st.expander(f"🍽️ {recipe.get('name', '요리')}"):
                                            st.write(recipe.get('description', ''))
                                            st.write("**조리 방법:**")
                                            for j, step in enumerate(recipe.get('steps', []), 1):
                                                st.write(f"{j}. {step}")
                        else:
                            st.error("분석 실패")
        
        with col2:
            st.subheader("🏋️ 운동기구 분석")
            exercise_image = st.file_uploader("운동기구/환경 사진", type=["jpg", "jpeg", "png"], key="ex_img")
            
            if exercise_image:
                st.image(exercise_image, use_container_width=True)
                target_area = st.selectbox("목표 부위", ["전신", "상체", "하체", "코어"])
                if st.button("🔍 운동기구 분석", type="primary"):
                    with st.spinner("🔬 분석 중..."):
                        init_analyzer()
                        analysis = st.session_state.analyzer.analyze_equipment(exercise_image.getvalue())
                        if analysis.get("success"):
                            st.success("✅ 분석 완료!")
                            st.markdown("### 🏋️ 인식된 기구")
                            for eq in analysis.get("equipment", []):
                                st.info(f"**{eq['name']}**")
                            
                            profile = create_profile()
                            with st.spinner("💪 루틴 생성 중..."):
                                routine = st.session_state.analyzer.suggest_exercises([e["name"] for e in analysis.get("equipment", [])], target_area, "중급", 30, profile.diseases)
                                if routine.get("success"):
                                    st.markdown(f"### 💪 {routine.get('routine_name')}")
                                    for ex in routine.get("main_workout", []):
                                        st.write(f"• **{ex['name']}**: {ex.get('sets')}세트 x {ex.get('reps')}")

    # ===== 탭3: 건강 분석 (복구됨) =====
    with tab3:
        st.header("📊 건강 상태 분석")
        if st.button("🔍 내 건강 점수 확인하기", type="primary"):
            profile = create_profile()
            health_data = {
                "protein_intake": profile.protein, "carb_intake": 300, "fat_intake": 65,
                "calories": profile.calories, "sleep_hours": profile.sleep_hours,
                "exercise_days": 3 if profile.activity_level in ["활발함", "매우활발함"] else 1,
                "stress_level": profile.stress_level, "water_intake": 1.5,
                "height": profile.height, "weight": profile.weight
            }
            analysis = st.session_state.xai.analyze_health_factors(health_data)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("건강 점수", f"{analysis['health_score']}점", analysis['status'])
            col2.metric("BMI", profile.bmi, profile.bmi_status)
            col3.metric("권장 칼로리", f"{profile.recommended_calories}kcal")
            
            if analysis["issues"]:
                st.markdown("### ⚠️ 개선 필요")
                for issue in analysis["issues"]: st.warning(f"• {issue}")
            if analysis["recommendations"]:
                st.markdown("### 💡 추천")
                for rec in analysis["recommendations"]: st.success(f"✓ {rec}")

    # ===== 탭4: 맞춤 추천 (핵심 수정!) =====
    with tab4:
        st.header("🍽️ 개인 맞춤 추천")
        profile = create_profile()
        st.info(f"**{profile.gender}, {profile.age}세** | BMI: {profile.bmi} ({profile.bmi_status}) | 목표: {profile.goal}")

        # ★ Tabs로 분리
        rec_tab1, rec_tab2 = st.tabs(["🥗 식단 추천", "💪 운동 추천"])

        # 1. 식단 추천 탭
        with rec_tab1:
            st.subheader("🥗 맞춤형 식단 가이드")
            if st.button("🍽️ 오늘의 식단 추천받기", type="primary", use_container_width=True):
                with st.spinner("🥦 식품안전나라 데이터 검색 중..."):
                    init_rag()
                    # ★ mode="food" 전달
                    result = st.session_state.rag.query(
                        f"{profile.goal}에 좋은 영양가 있는 식단 추천해줘", 
                        user_profile=profile,
                        search_categories=['food'],
                        mode="food"
                    )
                    st.markdown(result.get("answer", ""))
                    
                    if result.get("sources"):
                        with st.expander("📊 영양 성분 데이터 (출처: 식품안전나라 API)"):
                            for source in result.get("sources", []):
                                st.caption(f"- {source.get('title')} (출처: {source.get('source')})")

        # 2. 운동 추천 탭
        with rec_tab2:
            st.subheader("💪 맞춤형 운동 가이드")
            if st.button("🏃 오늘의 운동 추천받기", type="primary", use_container_width=True):
                with st.spinner("🏋️ 국민체력100 동영상 검색 중..."):
                    init_rag()
                    # ★ mode="exercise" 전달
                    result = st.session_state.rag.query(
                        f"{profile.goal}을 위한 {profile.activity_level} 수준의 운동 추천해줘", 
                        user_profile=profile,
                        search_categories=['video'],
                        mode="exercise"
                    )
                    st.markdown(result.get("answer", ""))
                    
                    if result.get("sources"):
                        st.divider()
                        st.markdown("### 📺 관련 운동 영상")
                        for source in result.get("sources", []):
                            video_url = source.get('video_url', '')
                            title = source.get('title', '운동 영상')
                            if video_url:
                                st.markdown(f"**[{title}]({video_url})**")

    # ===== 탭5: 사용법 (복구됨) =====
    with tab5:
        st.header("📖 사용 방법")
        st.markdown("""
        ## 🆕 FitLife AI 2.0 기능
        ### 📸 이미지 분석
        - **식재료 분석**: 냉장고 사진 → 재료 인식 → 요리 추천
        - **운동기구 분석**: 기구 사진 → 운동 루틴 추천
        ### 🗃️ 공공데이터
        - **국민체력100**: 500개+ 운동 데이터
        - **식품안전나라**: 100개+ 음식 데이터
        """)
    
    st.divider()
    st.caption("🏃 FitLife AI 2.0 | AI 기반 개인 맞춤형 건강 관리")

if __name__ == "__main__":
    main()
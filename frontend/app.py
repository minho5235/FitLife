"""FitLife AI 2.0 - 강화된 웹앱"""
import streamlit as st
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.rag.chain import FitLifeRAG
from src.xai.explainer import HealthExplainer
from src.models.user_profile import UserProfile
from src.vision.image_analyzer import ImageAnalyzer

st.set_page_config(page_title="FitLife AI 2.0", page_icon="🏃", layout="wide")

# 세션 상태
if "messages" not in st.session_state: st.session_state.messages = []
if "rag" not in st.session_state: st.session_state.rag = None
if "xai" not in st.session_state: st.session_state.xai = HealthExplainer()
if "analyzer" not in st.session_state: st.session_state.analyzer = None

def init_rag():
    if st.session_state.rag is None:
        with st.spinner("🔄 AI 초기화 중..."):
            st.session_state.rag = FitLifeRAG()

def init_analyzer():
    if st.session_state.analyzer is None:
        st.session_state.analyzer = ImageAnalyzer()

def create_profile() -> UserProfile:
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

# ===== 사이드바 =====
with st.sidebar:
    st.title("👤 내 프로필")
    
    with st.expander("📋 기본 정보", expanded=True):
        col1, col2 = st.columns(2)
        with col1: st.number_input("나이", 10, 100, 30, key="age")
        with col2: st.selectbox("성별", ["남성", "여성"], key="gender")
        col3, col4 = st.columns(2)
        with col3: st.number_input("키(cm)", 100.0, 220.0, 170.0, key="height")
        with col4: st.number_input("체중(kg)", 30.0, 200.0, 70.0, key="weight")
        
        profile = create_profile()
        bmi_color = "green" if profile.bmi_status == "정상" else "orange" if profile.bmi_status in ["과체중", "저체중"] else "red"
        st.markdown(f"**BMI: :{bmi_color}[{profile.bmi}]** ({profile.bmi_status})")
    
    with st.expander("🏥 건강 상태"):
        st.multiselect("질환", ["당뇨", "고혈압", "고지혈증", "위염", "관절염", "신장질환", "통풍"], key="diseases")
        st.multiselect("알러지", ["견과류", "갑각류", "유제품", "글루텐", "계란", "대두", "생선"], key="allergies")
    
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
    
    if profile.diseases or profile.allergies:
        st.warning(f"⚠️ 질환: {', '.join(profile.diseases) if profile.diseases else '없음'}\n🚫 알러지: {', '.join(profile.allergies) if profile.allergies else '없음'}")

# ===== 메인 =====
st.title("🏃 FitLife AI 2.0")
st.caption("AI 기반 개인 맞춤형 건강 관리 | 📸 이미지 분석 | 🍽️ 식단 추천 | 💪 운동 추천")

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
                result = st.session_state.rag.query(prompt, create_profile())
                response = result.get("answer", "죄송합니다. 답변을 생성할 수 없습니다.")
                st.markdown(response)
                
                if result.get("sources"):
                    with st.expander("📚 참고 자료"):
                        for src in result["sources"][:5]:
                            title = src.get("metadata", {}).get("title", "")
                            source = src.get("metadata", {}).get("source", "")
                            if title: st.caption(f"• {title} ({source})")
        
        st.session_state.messages.append({"role": "assistant", "content": response})

# ===== 탭2: 이미지 분석 =====
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
                            freshness = {"신선": "🟢", "보통": "🟡", "주의": "🔴"}.get(ing.get("freshness", "보통"), "⚪")
                            st.info(f"{freshness} **{ing['name']}** - {ing.get('quantity', '')} ({ing.get('category', '')})")
                        
                        # 요리 추천
                        ingredient_names = [ing["name"] for ing in analysis.get("ingredients", [])]
                        profile = create_profile()
                        restrictions = profile.allergies + profile.diseases
                        
                        with st.spinner("🍳 요리 추천 중..."):
                            recipes = st.session_state.analyzer.suggest_recipes(ingredient_names, restrictions, meal_type)
                            if recipes.get("success"):
                                st.markdown("### 🍳 추천 요리")
                                for recipe in recipes.get("recipes", []):
                                    with st.expander(f"🍽️ {recipe.get('name', '요리')}", expanded=True):
                                        st.write(f"**설명**: {recipe.get('description', '')}")
                                        st.write(f"**조리시간**: {recipe.get('cooking_time', '-')} | **난이도**: {recipe.get('difficulty', '-')}")
                                        nutrition = recipe.get("nutrition", {})
                                        if nutrition:
                                            c1, c2 = st.columns(2)
                                            c1.metric("칼로리", f"{nutrition.get('calories', '-')}kcal")
                                            c2.metric("단백질", f"{nutrition.get('protein', '-')}g")
                                        steps = recipe.get("steps", [])
                                        if steps:
                                            st.write("**조리 방법:**")
                                            for j, step in enumerate(steps, 1):
                                                st.write(f"{j}. {step}")
                    else:
                        st.error(f"❌ 분석 실패: {analysis.get('error', '알 수 없는 오류')}")
    
    with col2:
        st.subheader("🏋️ 운동기구 분석")
        exercise_image = st.file_uploader("운동기구/환경 사진", type=["jpg", "jpeg", "png"], key="ex_img")
        
        if exercise_image:
            st.image(exercise_image, use_container_width=True)
            target_area = st.selectbox("목표 부위", ["전신", "상체", "하체", "코어", "등", "가슴", "팔"])
            fitness_level = st.selectbox("운동 수준", ["초급", "중급", "고급"])
            duration = st.slider("운동 시간(분)", 10, 90, 30)
            
            if st.button("🔍 운동기구 분석", type="primary"):
                with st.spinner("🔬 분석 중..."):
                    init_analyzer()
                    analysis = st.session_state.analyzer.analyze_equipment(exercise_image.getvalue())
                    
                    if analysis.get("success"):
                        st.success("✅ 분석 완료!")
                        st.markdown("### 🏋️ 인식된 기구")
                        for eq in analysis.get("equipment", []):
                            st.info(f"**{eq['name']}** ({eq.get('category', '')})")
                        
                        env = analysis.get("environment", "")
                        if env: st.write(f"🏠 환경: {env}")
                        
                        # 운동 추천
                        equipment_names = [eq["name"] for eq in analysis.get("equipment", [])]
                        profile = create_profile()
                        
                        with st.spinner("💪 운동 루틴 생성 중..."):
                            routine = st.session_state.analyzer.suggest_exercises(equipment_names, target_area, fitness_level, duration, profile.diseases)
                            if routine.get("success"):
                                st.markdown(f"### 💪 {routine.get('routine_name', '맞춤 루틴')}")
                                st.caption(f"예상 소모 칼로리: {routine.get('estimated_calories', '-')}kcal")
                                
                                with st.expander("🔥 준비운동", expanded=True):
                                    for ex in routine.get("warmup", []):
                                        st.write(f"• **{ex['name']}** ({ex.get('duration', '')})")
                                
                                with st.expander("💪 본운동", expanded=True):
                                    for ex in routine.get("main_workout", []):
                                        st.write(f"• **{ex['name']}** - {ex.get('sets', '-')}세트 x {ex.get('reps', '-')} | 휴식 {ex.get('rest', '-')} | 부위: {ex.get('target_muscle', '')}")
                                
                                with st.expander("🧘 정리운동", expanded=True):
                                    for ex in routine.get("cooldown", []):
                                        st.write(f"• **{ex['name']}** ({ex.get('duration', '')})")
                    else:
                        st.error(f"❌ 분석 실패: {analysis.get('error', '')}")

# ===== 탭3: 건강 분석 =====
with tab3:
    st.header("📊 건강 상태 분석")
    
    if st.button("🔍 건강 분석", type="primary"):
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

# ===== 탭4: 맞춤 추천 =====
with tab4:
    st.header("🍽️ 개인 맞춤 추천")
    
    profile = create_profile()
    st.info(f"**{profile.gender}, {profile.age}세** | BMI: {profile.bmi} ({profile.bmi_status}) | 목표: {profile.goal}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🥗 음식 추천", type="primary", use_container_width=True):
            with st.spinner("검색 중..."):
                init_rag()
                result = st.session_state.rag.query(f"{profile.goal}에 좋은 건강한 음식 추천", profile)
                st.markdown(result.get("answer", ""))
    
    with col2:
        if st.button("💪 운동 추천", type="primary", use_container_width=True):
            with st.spinner("검색 중..."):
                init_rag()
                result = st.session_state.rag.query(f"{profile.goal}을 위한 {profile.activity_level} 활동량에 맞는 운동 추천", profile)
                st.markdown(result.get("answer", ""))

# ===== 탭5: 사용법 =====
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
    
    ### 🎯 개인 맞춤
    - 질환별 음식/운동 자동 필터링
    - 알러지 식품 자동 제외
    
    ---
    
    ## 사용 방법
    1. 왼쪽에서 **프로필** 설정
    2. **AI 상담**에서 질문
    3. **이미지 분석**으로 사진 기반 추천
    4. **건강 분석**으로 상태 점검
    
    ---
    
    ⚠️ 이 서비스는 의료 진단을 대체하지 않습니다.
    """)

st.divider()
st.caption("🏃 FitLife AI 2.0 | AI 기반 개인 맞춤형 건강 관리")

# FitLife

=======
<div align="center">
=======
# 🏃 FitLife AI 2.0

> **AI 기반 개인 맞춤형 건강 관리 시스템**
> 
> 📸 이미지 분석 | 🍽️ 식단 추천 | 💪 운동 추천 | 🏥 질환/알러지 필터링

---

## 🆕 v2.0 주요 기능

| 기능 | 설명 |
|------|------|
| **📸 이미지 분석** | 식재료/운동기구 사진 → AI 인식 → 맞춤 추천 |
| **🏥 건강 필터링** | 질환(당뇨, 고혈압 등) 고려한 자동 제외 |
| **🚫 알러지 관리** | 7가지 알러지 식품 자동 제외 |
| **📊 공공데이터** | 국민체력100 운동 500개+ |
| **🔍 XAI 분석** | 건강 점수 및 개선사항 시각화 |

---

## 📁 프로젝트 구조

```
FitLife/
├── frontend/
│   └── app.py              # Streamlit 웹앱
├── src/
│   ├── models/
│   │   └── user_profile.py # 사용자 프로필
│   ├── rag/
│   │   ├── chain.py        # RAG 체인
│   │   └── knowledge_base.py
│   ├── vision/
│   │   └── image_analyzer.py # 이미지 분석 (식재료+운동기구)
│   ├── xai/
│   │   └── explainer.py    # 건강 분석
│   ├── utils/
│   │   └── filters.py      # 건강 필터링
│   └── data/
│       └── public_data_loader.py # 공공데이터 연동
├── data/
│   ├── raw/                # 원본 데이터
│   └── processed/          # 국민체력100 데이터
├── load_knowledge.py       # 지식베이스 구축
├── test_all.py            # 통합 테스트
└── requirements.txt
```

---

## 🚀 시작하기

### 1. 환경 설정
```bash
conda activate fitlife-ai
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일:
```
GOOGLE_API_KEY=
FOOD_SAFETY_API_
DatabasePassword=
SUPABASE_URL=
SUPABASE_KEY=
DATABASE_URL=
```

### 3. 지식베이스 구축
```bash
python load_knowledge.py
```

### 4. 실행
```bash
streamlit run frontend/app.py
```

---

## 📊 데이터 출처

| 데이터 | 출처 | 개수 |
|--------|------|------|
| 음식 | 식품안전나라 | 100+ |
| 운동 | ACSM | 50+ |
| 운동 | 국민체력100 | 500+ |

---

## 💡 사용 예시

### AI 상담
```
"당뇨인데 저녁에 뭐 먹을까요?"
→ 고당류 식품 제외한 맞춤 추천
```

### 이미지 분석
```
[냉장고 사진 업로드]
→ 재료 인식: 닭가슴살, 브로콜리, 계란
→ 추천 요리: 닭가슴살 샐러드, 계란볶음밥...
```

---

## ⚠️ 주의사항

- 의료 진단을 대체하지 않습니다
- 심각한 증상은 전문의와 상담하세요

---

<div align="center">

**Made with ❤️ by Team FitLife**

</div>
=======
**🏃 FitLife AI 2.0** - 당신의 건강한 삶을 위한 AI 파트너

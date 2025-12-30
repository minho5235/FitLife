# 📐 FitLife AI 아키텍처 다이어그램

이 문서는 FitLife AI의 시스템 아키텍처를 설명합니다.

---

## 📁 다이어그램 파일 목록

| 파일명 | 설명 |
|--------|------|
| `architecture-main.mermaid` | 전체 시스템 구조 |
| `architecture-rag.mermaid` | RAG 파이프라인 상세 |
| `architecture-xai.mermaid` | XAI 분석 프로세스 |
| `architecture-stack.mermaid` | 기술 스택 구성 |

---

## 🔍 다이어그램 보는 방법

### 방법 1: GitHub에서 직접 보기
GitHub는 `.mermaid` 파일을 자동으로 렌더링합니다.

### 방법 2: Mermaid Live Editor
1. https://mermaid.live 접속
2. `.mermaid` 파일 내용 복사 & 붙여넣기
3. 이미지로 다운로드 (PNG/SVG)

### 방법 3: VS Code 확장
1. "Mermaid Preview" 확장 설치
2. `.mermaid` 파일 열기
3. 미리보기 실행

### 방법 4: 노션에서 보기
1. 노션 페이지에서 `/mermaid` 입력
2. 코드 블록에 내용 붙여넣기

---

## 🏗️ 아키텍처 설명

### 1. 전체 시스템 구조 (architecture-main.mermaid)

```
사용자 → Streamlit → FastAPI → RAG/XAI → Gemini/ChromaDB
```

**주요 레이어:**
- **Frontend Layer**: Streamlit 기반 웹 UI
- **Backend Layer**: FastAPI REST API 서버
- **AI/ML Layer**: RAG + XAI 모듈
- **Data Layer**: ChromaDB 벡터 DB + 지식베이스

### 2. RAG 파이프라인 (architecture-rag.mermaid)

```
질문 → 임베딩 → 벡터 검색 → 컨텍스트 구성 → LLM 생성 → 답변 + 출처
```

**단계별 설명:**
1. **Query Embedding**: 사용자 질문을 벡터로 변환
2. **Vector Search**: ChromaDB에서 유사 문서 검색
3. **Context 구성**: 검색된 문서 + 사용자 프로필 결합
4. **LLM Generation**: Gemini로 답변 생성
5. **Output**: 답변 + 참조 출처 + 신뢰도

### 3. XAI 분석 프로세스 (architecture-xai.mermaid)

```
건강 데이터 → 정규화 → 규칙 분석 → 기여도 계산 → 설명 생성
```

**분석 항목:**
- 단백질/탄수화물/지방 섭취율
- 수면 시간
- 운동 빈도
- 스트레스 수준
- BMI

### 4. 기술 스택 (architecture-stack.mermaid)

**Frontend**: Streamlit + Plotly
**Backend**: FastAPI + Pydantic
**AI/ML**: LangChain + ChromaDB + SHAP
**LLM**: Google Gemini + Embedding API
**Data**: Pandas + NumPy + Scikit-learn

---

## 📸 이미지 생성하기

Mermaid Live Editor에서 PNG/SVG로 내보내서 `docs/images/` 폴더에 저장하세요.

```bash
docs/images/
├── architecture-main.png
├── architecture-rag.png
├── architecture-xai.png
└── architecture-stack.png
```

README.md에서 이미지 참조:
```markdown
![시스템 아키텍처](docs/images/architecture-main.png)
```

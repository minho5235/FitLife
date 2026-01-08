# 공공데이터 다운로드 가이드

## 식품 영양성분
1. https://various.foodsafetykorea.go.kr/nutrient/
2. 엑셀 다운로드 → 이 폴더에 저장

## 운동 정보
1. https://data.go.kr → "국민체력100" 검색
2. CSV 다운로드 → 이 폴더에 저장

## 변환 방법
```bash
python -m src.data.public_data_loader convert-food -f data/downloads/파일명.csv
```

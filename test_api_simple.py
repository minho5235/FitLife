import requests

# 사용자님의 인증키 (I2790 사용)
API_KEY = "0a69e25b4aa64142adc0"
SERVICE_ID = "I2790" 
FOOD_NAME = "닭가슴살"

def check_api():
    # 요청 URL 만들기
    url = f"http://openapi.foodsafetykorea.go.kr/api/{API_KEY}/{SERVICE_ID}/json/1/1/DESC_KOR={FOOD_NAME}"
    
    print(f"📡 요청 URL: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"응답 코드: {response.status_code}")
        
        # ★ 여기가 핵심! (있는 그대로 텍스트를 출력)
        print("📄 [서버가 보낸 원본 내용]:")
        print(response.text)
        print("-" * 50)
        
        # JSON 변환 시도
        data = response.json()
        print("✅ JSON 변환 성공! (데이터가 정상입니다)")
        print(data)
        
    except Exception as e:
        print(f"❌ JSON 변환 실패! (이게 바로 '섞여서 오는' 원인입니다)")
        print(f"에러 내용: {e}")
        print("\n👉 위 [서버가 보낸 원본 내용]을 보세요.")
        print("   'INFO-100'이나 '인증키가 유효하지 않습니다'라고 적혀있다면 -> 1시간만 기다리세요!")

if __name__ == "__main__":
    check_api()
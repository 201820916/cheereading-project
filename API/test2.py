import requests

# --- 설정 ---
API_KEY = "07e9930c7ec0ee51ef29376b9beec5bc39b0469bd844720b2f7713af24b6ede5"
base_url = "http://data4library.kr/api/loanItemSrch"
# --- 설정 종료 ---

params = {
    'authKey': API_KEY,
    'pageNo': 1,
    'pageSize': 10, # 10개만 요청해서 테스트
    'format': 'json'
}

print("▶️ '인기대출도서 조회' API에 테스트 요청을 보냅니다...")

try:
    response = requests.get(base_url, params=params, timeout=10)
    
    # 서버로부터 받은 응답 상태 코드 출력 (정상: 200)
    print(f"✔️ HTTP 상태 코드: {response.status_code}")
    
    # 서버로부터 받은 응답 내용(JSON)을 그대로 출력
    print("✔️ 서버 응답 내용:")
    print(response.json())

except requests.exceptions.RequestException as e:
    print(f"❌ 요청 실패: 네트워크 오류가 발생했습니다.")
    print(e)
except ValueError: # .json() 변환 실패 시
    print("❌ 요청 실패: 서버가 JSON 형식이 아닌 응답을 보냈습니다.")
    print("--- 서버 원본 응답 ---")
    print(response.text)
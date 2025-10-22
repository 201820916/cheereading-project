import requests
import pandas as pd
import xml.etree.ElementTree as ET
from tqdm import tqdm
import time
import json

# --- 설정 부분 ---
# 1. 여기에 발급받은 실제 인증키를 입력하세요.
API_KEY = "07e9930c7ec0ee51ef29376b9beec5bc39b0469bd844720b2f7713af24b6ede5"

# 2. ISBN 목록이 담긴 입력 파일 이름
INPUT_FILENAME = "book_list_final_candidates.csv"

# 3. 최종 결과가 저장될 출력 파일 이름
OUTPUT_FILENAME = "book_details_results.csv"

# 4. API 요청 사이의 지연 시간 (초). 서버 부하를 줄이기 위해 필수적입니다.
REQUEST_DELAY = 0.1
# --- 설정 종료 ---


def get_book_details_from_api(api_key, isbn):
    """
    주어진 ISBN으로 '도서별 이용 분석' API를 호출하여 상세 정보를 사전(dict) 형태로 반환합니다.
    """
    base_url = "http://data4library.kr/api/usageAnalysisList"
    params = {'authKey': api_key, 'isbn13': isbn, 'format': 'xml'}
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        book_info = root.find('book')
        if book_info is None:
            return None # 해당 ISBN의 정보가 없는 경우

        # 키워드와 가중치를 딕셔너리로 묶어서 처리
        keywords_dict = {}
        keywords = root.findall('.//keywords/keyword')
        if keywords:
            for keyword in keywords:
                word = keyword.findtext('word', '').strip()
                weight = keyword.findtext('weight', '').strip()
                if word and weight:
                    keywords_dict[word] = weight
        
        # 결과를 딕셔너리로 정리하여 반환
        return {
            'isbn': isbn,
            'title': book_info.findtext('bookname', '정보 없음').strip(),
            'authors': book_info.findtext('authors', '정보 없음').strip(),
            'genre': book_info.findtext('class_nm', '정보 없음').strip(),
            'publication_year': book_info.findtext('publication_year', '정보 없음').strip(),
            'description': book_info.findtext('description', '정보 없음').strip(),
            'cover_image_url': book_info.findtext('bookImageURL', '정보 없음').strip(),
            # json.dumps를 사용해 딕셔너리를 문자열로 변환하여 CSV에 저장
            'keywords': json.dumps(keywords_dict, ensure_ascii=False) if keywords_dict else '정보 없음'
        }
        
    except (requests.exceptions.RequestException, ET.ParseError):
        # 네트워크 오류나 XML 파싱 오류 발생 시 None 반환
        return None

def main():
    """
    메인 실행 함수
    """
    if API_KEY == "YOUR_API_KEY":
        print("⚠️  경고: API_KEY를 실제 발급받은 키로 변경해주세요.")
        return

    try:
        # 1. 입력 CSV 파일 읽기
        df_isbns = pd.read_csv(INPUT_FILENAME)
        if 'ISBN' not in df_isbns.columns:
            print(f"❌ 오류: '{INPUT_FILENAME}' 파일에 'ISBN' 열이 없습니다.")
            return
        isbn_list = df_isbns['ISBN'].dropna().astype(str).tolist()
        print(f"'{INPUT_FILENAME}' 파일에서 {len(isbn_list)}개의 ISBN을 성공적으로 읽었습니다.")
    except FileNotFoundError:
        print(f"❌ 오류: '{INPUT_FILENAME}' 파일을 찾을 수 없습니다. 스크립트와 같은 폴더에 있는지 확인해주세요.")
        return

    # 2. 각 ISBN에 대해 API를 호출하여 정보 수집
    results = []
    print(f"총 {len(isbn_list)}개의 도서 정보를 수집합니다...")
    
    for isbn in tqdm(isbn_list, desc="📚 도서 정보 수집 중"):
        book_data = get_book_details_from_api(API_KEY, isbn)
        if book_data:
            results.append(book_data)
        time.sleep(REQUEST_DELAY) # 서버에 부담을 주지 않기 위해 잠시 대기

    # 3. 수집된 결과를 DataFrame으로 변환하고 CSV 파일로 저장
    if not results:
        print("\nℹ️  수집된 도서 정보가 없습니다. API 키나 ISBN 목록을 확인해주세요.")
        return
        
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 성공! 총 {len(df_results)}개의 도서 정보를 '{OUTPUT_FILENAME}' 파일로 저장했습니다.")


if __name__ == "__main__":
    main()
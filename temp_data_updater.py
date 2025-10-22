# read_test.py
import csv

# 확인할 CSV 파일 이름
CSV_FILE = 'book_data.csv'

def test_csv_reading():
    """
    CSV 파일을 열어 처음 10줄의 ISBN과 title을 출력하여
    파일 읽기 과정 자체를 테스트합니다.
    """
    print(f"--- '{CSV_FILE}' 파일 읽기 테스트 시작 ---")
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            print("파일의 처음 10줄에서 ISBN과 title을 읽습니다...")
            
            count = 0
            for row in reader:
                if count >= 10:
                    break
                
                isbn_val = row.get('ISBN')
                title_val = row.get('title')
                
                print(f"  - [행 {count+1}] ISBN: {isbn_val}, Title: {title_val}")
                
                count += 1

            print(f"\n테스트 완료: 총 {count}줄을 성공적으로 읽었습니다.")

    except FileNotFoundError:
        print(f"❌ 오류: '{CSV_FILE}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 오류: 파일을 읽는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    test_csv_reading()
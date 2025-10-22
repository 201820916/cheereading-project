import pandas as pd
import numpy as np

# --- 1. 파일 경로 설정 ---
input_csv_path = 'book_data.csv'
output_csv_path = 'book_data_cleaned.csv'

print(f"🧹 '{input_csv_path}' 파일의 데이터 정제를 시작합니다...")

try:
    # --- 2. CSV 파일 불러오기 ---
    # 빈 값을 확실히 처리하기 위해 na_filter=False 옵션을 사용하지 않음
    df = pd.read_csv(input_csv_path)
    original_row_count = len(df)
    print(f"원본 데이터: 총 {original_row_count} 행")

    # --- 3. 정제 조건 정의 ---
    # 각 열의 데이터 타입을 문자열로 바꿔서 길이(len) 계산 시 오류 방지
    # 비어있는(NaN) 값은 빈 문자열('')로 안전하게 처리
    df['title'] = df['title'].astype(str).fillna('')
    df['author'] = df['author'].astype(str).fillna('')

    # 조건 1: 'title' 열의 길이가 255자를 초과하는 행
    condition_title = df['title'].str.len() > 255
    # 조건 2: 'author' 열의 길이가 255자를 초과하는 행
    condition_author = df['author'].str.len() > 255

    # [핵심] 위 두 조건 중 하나라도 해당하는 행을 '삭제할 행'으로 식별
    rows_to_delete = df[condition_title | condition_author]
    deleted_row_count = len(rows_to_delete)

    if deleted_row_count > 0:
        print(f"\n🗑️ 삭제될 행 {deleted_row_count}개를 찾았습니다:")
        # 삭제될 행의 제목 일부를 보여줘서 사용자가 확인할 수 있도록 함
        for title in rows_to_delete['title'].head(): # 최대 5개만 예시로 출력
            print(f"  - {title[:70]}...")
    else:
        print("\n✅ 삭제할 비정상적인 행이 없습니다.")

    # --- 4. 문제 있는 행 삭제 ---
    # [핵심] 위 조건에 해당하지 않는, 즉 '정상적인' 행들만 선택하여 새로운 데이터프레임 생성
    cleaned_df = df[~(condition_title | condition_author)]
    cleaned_row_count = len(cleaned_df)

    # --- 5. 정제된 데이터를 새 파일로 저장 ---
    print(f"\n💾 정제된 데이터 {cleaned_row_count} 행을 '{output_csv_path}' 파일로 저장합니다...")
    cleaned_df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

    print("\n✨ 데이터 정제가 완료되었습니다!")
    print(f"총 {deleted_row_count}개의 비정상적인 행이 삭제되었습니다.")

except FileNotFoundError:
    print(f"[오류] '{input_csv_path}' 파일을 찾을 수 없습니다. 파일 이름을 확인해주세요.")
except Exception as e:
    print(f"처리 중 오류가 발생했습니다: {e}")
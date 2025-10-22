#!/usr/bin/env bash
# exit on error
set -e

# 1. 필요한 파이썬 라이브러리 설치
pip install -r requirements.txt

# 2. (1단계에서 확보한) 원본 데이터 다운로드
#    아래 "YOUR_DIRECT_DOWNLOAD_LINK" 부분을 실제 링크로 바꾸세요.
echo "Downloading source data..."
curl -L "YOUR_DIRECT_DOWNLOAD_LINK" -o book_details_results.csv

# 3. 파이썬 스크립트를 실행해 FAISS 인덱스 파일 생성
echo "Building FAISS index..."
python build_faiss_index.py

# 4. Django 정적 파일 수집 (이것도 빌드 과정에 포함)
echo "Running collectstatic..."
python manage.py collectstatic --noinput
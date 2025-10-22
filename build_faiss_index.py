# build_faiss_index.py

import os
import django
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer # 이 import가 있는지 확인

# Django 환경 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cheereading.settings")
django.setup()

from books.models import Book

def build_index():
    print("모든 책 데이터를 불러오는 중...")
    books = list(Book.objects.all())

    if not books:
        print("데이터베이스에 책이 없습니다. 스크립트를 종료합니다.")
        return

    print("임베딩 모델을 불러오는 중...")
    # ▼▼▼ [수정] 모델 이름의 오타를 'multitask'로 수정합니다. ▼▼▼
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')

    print("책 데이터를 벡터로 변환하는 중... (시간이 걸릴 수 있습니다)")
    # 저장된 임베딩 벡터를 재사용하는 것이 더 효율적입니다.
    embeddings = np.array([book.embedding_vector for book in books if book.embedding_vector]).astype('float32')
    book_ids = np.array([book.id for book in books if book.embedding_vector])
    
    if len(embeddings) == 0:
        print("임베딩 벡터가 있는 책이 없습니다. 'generate_embeddings.py'를 먼저 실행해주세요.")
        return

    # FAISS 인덱스 생성
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIDMap(index)

    print("FAISS 인덱스를 빌드하는 중...")
    index.add_with_ids(embeddings, book_ids)

    # 인덱스 파일 저장
    faiss.write_index(index, "book_index.faiss")
    print(f"✅ 성공: {index.ntotal}개의 책에 대한 인덱스를 'book_index.faiss' 파일로 저장했습니다.")

if __name__ == "__main__":
    build_index()
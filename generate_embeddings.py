import os
import django
import numpy as np
from sentence_transformers import SentenceTransformer
import ast # 문자열로 저장된 키워드를 리스트로 변환하기 위해 추가

# --- Django 환경 설정 ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cheereading.settings')
django.setup()
# -------------------------

from books.models import Book

def run():
    print("Loading sentence-transformer model (jhgan/ko-sroberta-multitask)...")
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    print("Model loaded.")

    # [수정] 벡터가 없거나, 새로 추가된 책을 모두 포함하도록 로직 변경 가능
    # 여기서는 기존과 같이 벡터가 없는 책만 처리하도록 유지
    books_to_update = Book.objects.filter(embedding_vector__isnull=True)
    total_count = books_to_update.count()
    if total_count == 0:
        print("✅ All books already have embedding vectors.")
        return
        
    print(f"Found {total_count} books to process. Starting generation...")

    for i, book in enumerate(books_to_update):
        # ▼▼▼ [핵심 수정] 임베딩을 위한 텍스트 조합 ▼▼▼

        # 1. 장르 정보 가져오기 (M2M 필드)
        # book.genres.all()을 통해 연결된 모든 장르 객체를 가져와서, 각 장르의 이름을 리스트로 만듭니다.
        genre_names = [genre.name for genre in book.genres.all()]
        genre_text = " ".join(genre_names) # 예: "IT 전문서적 컴퓨터 공학"

        # 2. 키워드 정보 가져오기 (JSON/TextField)
        # 데이터베이스에 "[{'word': '파이썬', 'weight': 10.0}, ...]" 형태로 저장된 키워드를 처리합니다.
        keyword_text = ""
        if book.keywords:
            try:
                # 문자열 형태의 데이터를 실제 파이썬 리스트로 안전하게 변환
                keywords_list = ast.literal_eval(book.keywords) if isinstance(book.keywords, str) else book.keywords
                # 리스트에서 'word' 값만 추출하여 합칩니다.
                if isinstance(keywords_list, list):
                    keyword_text = " ".join([item.get('word', '') for item in keywords_list])
            except (ValueError, SyntaxError):
                # 데이터 형식이 잘못된 경우를 대비한 예외 처리
                keyword_text = ""

        # 3. 모든 정보를 조합하여 최종 텍스트 생성
        # "제목. 줄거리. 장르들. 키워드들." 형태로 텍스트를 구성하여 AI에 전달합니다.
        text_to_embed = f"{book.title}. {book.summary or ''}. {genre_text}. {keyword_text}"
        
        # ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲

        vector = model.encode(text_to_embed)
        
        book.embedding_vector = vector.tolist()
        book.save(update_fields=['embedding_vector'])
        
        print(f"  ({i+1}/{total_count}) Generated vector for: {book.title}")

    print("\n✨ Embedding vector generation complete!")

if __name__ == '__main__':
    try:
        import sentence_transformers
    except ImportError:
        print("[ERROR] 'sentence-transformers' is not installed.")
        print("Please run: pip install sentence-transformers")
    else:
        run()
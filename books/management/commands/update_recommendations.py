import numpy as np
import faiss
from django.core.management.base import BaseCommand
from sentence_transformers import SentenceTransformer
from books.models import Book
# import json # json은 이제 JSONField를 사용하므로 필요 없습니다.

class Command(BaseCommand):
    help = 'Updates book vectors and FAISS index for recommendations'

    def handle(self, *args, **options):
        # ... (모델 로드, 책 가져오기, 텍스트 변환 로직은 동일) ...
        self.stdout.write('Loading Sentence-BERT model...')
        model = SentenceTransformer('jhgan/ko-sroberta-multitask')

        self.stdout.write('Fetching books from database...')
        books = list(Book.objects.all())
        book_ids = [book.id for book in books]

        self.stdout.write('Preprocessing book data...')
        book_texts = [f"{book.description or ''}. {book.genre or ''}." for book in books]

        self.stdout.write('Encoding books to vectors... This may take a while.')
        book_vectors = model.encode(book_texts, convert_to_tensor=False, show_progress_bar=True)

        # --- 수정된 부분 ---
        self.stdout.write('Saving vectors to database...')
        for book, vector in zip(books, book_vectors):
            book.embedding_vector = vector.tolist()  # numpy 배열을 파이썬 리스트로 변환하여 저장
            book.save()
        # --------------------

        self.stdout.write('Building FAISS index...')
        embedding_dim = book_vectors.shape[1]
        index = faiss.IndexFlatL2(embedding_dim)
        index = faiss.IndexIDMap(index)
        book_ids_np = np.array(book_ids, dtype=np.int64)
        index.add_with_ids(book_vectors, book_ids_np)

        faiss.write_index(index, 'book_index.faiss')
        self.stdout.write(self.style.SUCCESS(f'Successfully created index and saved vectors for {index.ntotal} books.'))
# books/management/commands/link_genres.py

from django.core.management.base import BaseCommand
from books.models import Book, Genre
import time

class Command(BaseCommand):
    help = 'Links books to genres based on their KDC code'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to link genres to books...'))
        start_time = time.time()

        # KDC 코드 앞자리와 장르 이름을 연결하는 규칙 (매핑)
        # KDC 코드 데이터에 kdc1 필드가 있다고 가정합니다. 필드명이 다르면 수정해야 합니다.
        kdc_to_genre_map = {
            '0': '총류',
            '1': '철학',
            '2': '종교',
            '3': '사회과학',
            '4': '자연과학',
            '5': '기술과학',
            '6': '예술',
            '7': '언어',
            '8': '문학',
            '9': '역사',
        }

        # 장르 객체를 미리 불러와서 데이터베이스 조회를 줄입니다.
        genres = {genre.name: genre for genre in Genre.objects.all()}
        
        books_processed = 0
        books_linked = 0

        # 메모리를 효율적으로 사용하기 위해 iterator() 사용
        for book in Book.objects.all().iterator():
            books_processed += 1
            # 책에 kdc_code 필드가 있다고 가정. 필드명이 다르면 이 부분을 수정해야 합니다.
            kdc_code = getattr(book, 'kdc_code', None)

            if kdc_code and isinstance(kdc_code, str) and len(kdc_code) > 0:
                main_category_code = kdc_code[0]
                genre_name = kdc_to_genre_map.get(main_category_code)
                
                if genre_name and genre_name in genres:
                    genre_obj = genres[genre_name]
                    # 책의 genres 필드에 해당 장르를 추가합니다.
                    book.genres.add(genre_obj)
                    books_linked += 1

            if books_processed % 1000 == 0:
                self.stdout.write(f'{books_processed} books processed...')

        end_time = time.time()
        duration = end_time - start_time

        self.stdout.write(self.style.SUCCESS(
            f'Successfully finished linking genres. '
            f'Processed: {books_processed} books. '
            f'Linked: {books_linked} books. '
            f'Duration: {duration:.2f} seconds.'
        ))
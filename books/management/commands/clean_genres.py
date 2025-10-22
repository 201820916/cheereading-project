import csv
from django.core.management.base import BaseCommand
from books.models import Book, Genre

class Command(BaseCommand):
    help = 'Maps KDC genres to simple categories for all books.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting genre mapping process based on KDC codes...")

        KDC_MAP = {
            '1': '인문', '2': '인문', 
            '3': '경제/경영',
            '4': '과학', '5': '과학',
            '8': '소설', # '시/에세이'는 아래에서 세부 조정
            '9': '역사', # '여행'은 아래에서 세부 조정
        }

        processed_count = 0
        for book in Book.objects.all():
            if book.kdc_code: # KDC 코드가 있는 경우에만 실행
                try:
                    first_digit = str(book.kdc_code).strip()[0]
                    simple_genre_name = KDC_MAP.get(first_digit)

                    if simple_genre_name:
                        # KDC 800번대(문학) 중에서 '시'인 경우 세부 조정
                        if first_digit == '8' and any('시' in g.name for g in book.genres.all()):
                            simple_genre_name = '시/에세이'
                        
                        # KDC 900번대(역사) 중에서 '여행'인 경우 세부 조정
                        if first_digit == '9' and any('여행' in g.name for g in book.genres.all()):
                            simple_genre_name = '여행'

                        genre_obj, _ = Genre.objects.get_or_create(name=simple_genre_name)
                        book.genres.add(genre_obj)
                        processed_count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  > Error processing '{book.title}': {e}"))

        self.stdout.write(self.style.SUCCESS(f"Genre mapping complete! {processed_count} books were tagged."))
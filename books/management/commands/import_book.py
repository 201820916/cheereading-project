import pandas as pd
import os  # 👈 os 임포트
from django.conf import settings  # 👈 settings 임포트
from django.core.management.base import BaseCommand
from books.models import Book, Genre
# ❌ requests, StringIO는 더 이상 필요 없으므로 삭제


class Command(BaseCommand):
    help = 'Import books from a local CSV file (book_details_results.csv) into the database'

    def handle(self, *args, **kwargs):
        
        # 🔹 GitHub에 업로드한 로컬 파일 경로 설정
        csv_file_name = 'book_details_results.csv'
        csv_file_path = os.path.join(settings.BASE_DIR, csv_file_name)

        self.stdout.write(self.style.SUCCESS(f"Loading CSV data from local file: {csv_file_path}"))

        try:
            # 🔹 GCS/Google Drive 로직 대신, 파일 경로에서 직접 읽기
            df = pd.read_csv(csv_file_path) 
            df = df.where(pd.notnull(df), None) # NaN 값을 None으로 변경
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ ERROR: File not found at {csv_file_path}"))
            self.stdout.write(self.style.ERROR("Ensure 'book_details_results.csv' is in the root directory of your project."))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to load or read CSV file: {e}"))
            return

        self.stdout.write(self.style.SUCCESS(f"✅ Loaded {len(df)} rows from '{csv_file_name}'"))
        self.stdout.write(self.style.SUCCESS(f"Starting to import {len(df)} books..."))

        for index, row in df.iterrows():
            title = row.get('title')
            if not title:
                self.stdout.write(self.style.WARNING(f"⚠️ Skipping row {index + 2} due to empty title."))
                continue

            cover_url_from_csv = row.get('cover_image_url')

            defaults_data = {
                'publication_year': self.clean_year(row.get('publication_year')),
                'summary': row.get('description'),
                'keywords': row.get('keywords'),
                'isbn13': self.clean_isbn(row.get('isbn')),
                'cover_image_url': cover_url_from_csv,
            }

            book_obj, created = Book.objects.update_or_create(
                title=title,
                author=row.get('authors'),
                defaults=defaults_data
            )

            # DB 확인용 로그 (원본 코드와 동일)
            book_from_db = Book.objects.get(id=book_obj.id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  > [DB CHECK] '{title[:30]}...' cover_url in DB: {book_from_db.cover_image_url}"
                )
            )

            # 장르 처리 (원본 코드와 동일)
            genre_str = row.get('genre')
            if genre_str and book_obj:
                genre_names = [name.strip() for name in str(genre_str).split(',')]
                book_obj.genres.clear()
                for name in genre_names:
                    if name:
                        genre_obj, _ = Genre.objects.get_or_create(name=name)
                        book_obj.genres.add(genre_obj)

        self.stdout.write(self.style.SUCCESS("🎉 Import complete!"))

    # ---------------------------------------------------------
    # Helper functions (원본 코드와 동일)
    # ---------------------------------------------------------
    def clean_year(self, year):
        if year is None:
            return None
        try:
            return int(float(year))
        except (ValueError, TypeError):
            return None

    def clean_isbn(self, isbn):
        if isbn is None:
            return None
        try:
            clean_isbn_str = str(int(float(str(isbn))))
            return clean_isbn_str if len(clean_isbn_str) <= 13 else None
        except (ValueError, TypeError):
            return None

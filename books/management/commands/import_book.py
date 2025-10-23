import pandas as pd
import requests
from io import StringIO
from django.core.management.base import BaseCommand
from books.models import Book, Genre


class Command(BaseCommand):
    help = 'Import books from a CSV file into the database (supports Google Drive)'

    def handle(self, *args, **kwargs):
        # 🔹 Google Drive 공유 링크를 직접 다운로드 가능한 형태로 변환
        url = "https://drive.google.com/uc?export=download&id=1HHyLKBosiPkHkiJDzTVmiI_0UhVeDxdz"

        self.stdout.write(self.style.SUCCESS(f"Downloading CSV data from Google Drive..."))

        try:
            response = requests.get(url)
            response.raise_for_status()  # 200이 아니면 예외 발생
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data, engine='python')
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to load CSV from Google Drive: {e}"))
            return

        self.stdout.write(self.style.SUCCESS(f"✅ Loaded {len(df)} rows from Google Drive CSV"))
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

            # DB 확인용 로그
            book_from_db = Book.objects.get(id=book_obj.id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  > [DB CHECK] '{title[:30]}...' cover_url in DB: {book_from_db.cover_image_url}"
                )
            )

            # 장르 처리
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
    # Helper functions
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

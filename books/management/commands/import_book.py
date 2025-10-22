import pandas as pd
from django.core.management.base import BaseCommand
from books.models import Book, Genre

class Command(BaseCommand):
    help = 'Import books from a CSV file into the database'

    def handle(self, *args, **kwargs):
        csv_path = 'book_details_results.csv'
        self.stdout.write(self.style.SUCCESS(f"Reading data from '{csv_path}'..."))

        try:
            df = pd.read_csv(csv_path, engine='python')
            df = df.where(pd.notnull(df), None)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Starting to import {len(df)} books..."))

        for index, row in df.iterrows():
            title = row.get('title')
            if not title:
                self.stdout.write(self.style.WARNING(f"Skipping row {index + 2} due to empty title."))
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

            # ▼▼▼ [핵심] 저장 직후, DB에서 값을 다시 읽어와 확인합니다. ▼▼▼
            book_from_db = Book.objects.get(id=book_obj.id)
            self.stdout.write(self.style.SUCCESS(f"  > [DB CHECK] For book '{title[:20]}...', cover_url in DB is: {book_from_db.cover_image_url}"))
            # ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲ ▲▲▲

            genre_str = row.get('genre')
            if genre_str and book_obj:
                genre_names = [name.strip() for name in str(genre_str).split(',')]
                book_obj.genres.clear()
                for name in genre_names:
                    if name:
                        genre_obj, _ = Genre.objects.get_or_create(name=name)
                        book_obj.genres.add(genre_obj)

        self.stdout.write(self.style.SUCCESS("Import complete!"))

    # ... (clean_year, clean_isbn 함수는 그대로 유지) ...
    def clean_year(self, year):
        if year is None: return None
        try: return int(float(year))
        except (ValueError, TypeError): return None

    def clean_isbn(self, isbn):
        if isbn is None: return None
        try:
            clean_isbn_str = str(int(float(str(isbn))))
            return clean_isbn_str if len(clean_isbn_str) <= 13 else None
        except (ValueError, TypeError): return None
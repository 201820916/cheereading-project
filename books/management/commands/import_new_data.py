import csv
import json
from django.core.management.base import BaseCommand
from books.models import Book, Genre

class Command(BaseCommand):
    help = 'Imports new book data from a CSV file and updates the database.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to import.')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        self.stdout.write(self.style.SUCCESS(f"Starting import from {csv_file_path}..."))

        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                updated_count = 0
                created_count = 0
                skipped_count = 0

                for row in reader:
                    try:
                        title = row.get('title')
                        author = row.get('author')
                        
                        if not title or not author:
                            self.stdout.write(self.style.WARNING(f"  > Skipping row with missing title or author."))
                            skipped_count += 1
                            continue

                        book, created = Book.objects.get_or_create(title=title, author=author)
                        
                        keywords_str = row.get('keywords', '')
                        weights_str = row.get('weights', '')
                        
                        if keywords_str and weights_str:
                            keywords = keywords_str.split('|')
                            weights = weights_str.split('|')
                            merged_list = [{'word': word, 'weight': weight} for word, weight in zip(keywords, weights)]
                            book.keywords = json.dumps(merged_list, ensure_ascii=False)

                        publication_year = row.get('publication_year')
                        if publication_year:
                            book.publication_year = int(publication_year)
                        
                        book.summary = row.get('summary', '')

                        genre_str = row.get('genre', '').strip()
                        if genre_str:
                            book.kdc_code = genre_str

                        book.save()

                        if genre_str:
                            genre_obj, _ = Genre.objects.get_or_create(name=genre_str)
                            book.genres.add(genre_obj)

                        if created:
                            created_count += 1
                            self.stdout.write(f"  > Created: '{book.title}'")
                        else:
                            updated_count += 1
                            self.stdout.write(f"  > Updated: '{book.title}'")

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  > An error occurred with row for '{row.get('title', 'Unknown Title')}': {e}"))
                        skipped_count += 1

            self.stdout.write(self.style.SUCCESS(
                f"\nImport finished. {created_count} created, {updated_count} updated, {skipped_count} skipped."
            ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: The file '{csv_file_path}' was not found."))
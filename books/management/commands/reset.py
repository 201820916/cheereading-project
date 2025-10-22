# books/management/commands/reset_library.py  (또는 reset.py)

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from books.models import ReadingEntry

User = get_user_model()

# ▼▼▼ 클래스 이름이 반드시 "Command" 여야 합니다. (대소문자 중요) ▼▼▼
class Command(BaseCommand):
    help = 'Deletes all reading entries for a specific user.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='The username of the user whose library will be reset.')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        try:
            user = User.objects.get(username=username)
            entries_deleted, _ = ReadingEntry.objects.filter(user=user).delete()
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully deleted {entries_deleted} reading entries for user '{username}'."
            ))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with username '{username}' does not exist."))
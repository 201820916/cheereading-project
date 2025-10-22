# books/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="장르")

    def __str__(self):
        return self.name


class Book(models.Model):
    # book_id는 자동 생성되므로 명시할 필요 없음
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    cover_image_url = models.CharField(max_length=2083, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name="books", blank=True)
   # CharField를 TextField로 변경하고, max_length 옵션은 삭제합니다.
    keywords = models.TextField(blank=True, null=True)
    isbn13 = models.CharField(max_length=13, unique=True, null=True, blank=True)
    embedding_vector = models.JSONField(null=True, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    summary = models.TextField(blank=True, null=True)
    kdc_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="KDC 분류코드")

    # Meta 클래스는 db_table 이름이 모델이름_소문자와 다를 경우에만 명시
    class Meta:
        db_table = 'book'

    def __str__(self):
        return self.title

class ReadingEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review = models.TextField(blank=True)
    detailed_review = models.TextField(blank=True, null=True)
    read_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
    def __str__(self):
        return f"{self.user.username}'s review for {self.book.title}"
    

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.book.title}"


class BookRecommend(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # on_delete 수정
    book = models.ForeignKey('Book', on_delete=models.CASCADE)      # on_delete 수정
    rank = models.IntegerField(db_column='RANK', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    generated_time = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'book_recommend'

class Keyword(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_keywords')
    word = models.CharField(max_length=100)
    weight = models.IntegerField()

    def __str__(self):
        return f'{self.word} ({self.book.title})'
    

class UserFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    is_interested = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
    def __str__(self):
        return f"Feedback from {self.user.username} for {self.book.title}"
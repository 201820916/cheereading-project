# books/admin.py

from django.contrib import admin
from .models import Book, Genre, ReadingEntry # 필요한 모델들을 import

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # 1. 목록 페이지(List View)에 보여줄 필드를 설정합니다.
    # [수정] publication_year를 추가하여 목록에 보이게 합니다.
    list_display = ('title', 'author', 'publisher', 'publication_year')
    
    # 2. 검색 기능을 추가합니다.
    search_fields = ('title', 'author', 'ISBN')
    
    # 3. 상세 정보/수정 페이지(Detail View)에 보여줄 필드를 설정합니다.
    # [수정] Description과 Cover image url을 제외하고 필요한 필드만 나열합니다.
    fields = (
        'title', 
        'author', 
        'publisher', 
        'publication_year', 
        'genres', 
        'keywords', 
        'ISBN', 
        'summary', 
        'kdc_code',
        'embedding_vector'
    )
    
    # ManyToMany 필드(genres)를 더 편하게 선택할 수 있도록 필터 UI를 추가합니다.
    filter_horizontal = ('genres',)

# 다른 모델들도 필요하다면 여기에 등록할 수 있습니다.
admin.site.register(Genre)
admin.site.register(ReadingEntry)
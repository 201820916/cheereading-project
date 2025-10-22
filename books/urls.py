# books/urls.py

from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.book_search, name='search'),
    path('<int:book_id>/', views.book_detail, name='book_detail'),
    path('my-library/', views.my_library_view, name='my_library'),

    # ▼▼▼ [수정 1] 'add_review' 경로의 이름을 'add_reading_entry'로 변경합니다. ▼▼▼
    # 이렇게 하면 템플릿에서 {% url 'books:add_reading_entry' ... %}를 사용할 수 있습니다.
    path('review/add/<int:book_id>/', views.add_review, name='add_reading_entry'),
    
    # path('review/add/plan/<int:book_id>/', views.add_reading_entry_from_plan, name='add_reading_entry_from_plan'),
    path('review/edit/<int:entry_id>/', views.edit_reading_entry, name='edit_reading_entry'),
    
    # ▼▼▼ [수정 2] '내 서재에서 제거' 기능을 위한 URL을 'delete_reading_entry'로 바로잡습니다. ▼▼▼
    # 템플릿에서도 이 이름과 entry_id를 사용해야 합니다.
    path('review/delete/<int:entry_id>/', views.delete_reading_entry, name='delete_reading_entry'),
    
    path('wishlist/add/<int:book_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:book_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('recommendations/', views.recommend_books, name='recommendations'),
    path('feedback/<int:book_id>/', views.record_feedback, name='record_feedback'),
    path('review/add/from-plan/<int:book_id>/', views.add_reading_entry_from_plan, name='add_reading_entry_from_plan'),
    # ▼▼▼ [수정 3] 이전에 추가했던, 문제가 있는 URL 경로들을 모두 삭제합니다. ▼▼▼
]
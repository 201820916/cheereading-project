# plans/urls.py
from django.urls import path
from . import views

app_name = 'plans'

urlpatterns = [
    # '/plans/' : 플랜 목록 보기
    path('', views.plan_list, name='plan_list'),
    
    # '/plans/create/' : 새 플랜 만들기
    path('create/', views.plan_create, name='plan_create'),
    
    # '/plans/<plan_id>/' : 플랜 상세 보기
    path('<int:plan_id>/', views.plan_detail, name='plan_detail'),
    
    # '/plans/<plan_id>/update/' : 플랜 수정
    path('<int:plan_id>/update/', views.plan_update, name='plan_update'),
    
    # '/plans/<plan_id>/delete/' : 플랜 삭제
    path('<int:plan_id>/delete/', views.plan_delete, name='plan_delete'),
    
    # '/plans/<plan_id>/remove_book/<book_id>/' : 플랜에서 책 제거
    path('<int:plan_id>/remove_book/<int:book_id>/', views.remove_book_from_plan, name='remove_book'),

    # '/plans/api/book-search/' : AJAX 도서 검색 API
    path('api/book-search/', views.book_search_api, name='book_search_api'),

    # '/plans/<plan_id>/toggle-bookmark/' : 플랜 북마크 토글
    path('<int:plan_id>/toggle-bookmark/', views.toggle_bookmark, name='toggle_bookmark'),

    # '/plans/progress/' : 플랜 진행 상황 보기
    path('progress/toggle/<int:plan_book_id>/', views.toggle_book_progress, name='toggle_book_progress'),
    
    # '/plans/progress/' : 플랜 진행 상황 보기
    path('complete/<int:plan_id>/', views.complete_plan, name='complete_plan'),

    # '/plans/my_plans/' : 나의 플랜 / 북마크한 플랜 보기
    path('my-plans/', views.my_plans, name='my_plans'),

    path('<int:plan_id>/feedback/', views.save_plan_feedback, name='save_plan_feedback'),
    path('progress/update/<int:plan_id>/<int:book_id>/', views.update_plan_progress, name='update_plan_progress'),
]

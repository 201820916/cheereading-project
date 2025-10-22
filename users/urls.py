# users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomPasswordResetForm, CustomAuthenticationForm

app_name = 'users'

urlpatterns = [
    # --- 인증 관련 URL ---
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html', 
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/done/', views.signup_done, name='signup_done'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    
    # --- 프로필 관련 URL ---
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    
    # --- 비밀번호 재설정 및 ID 찾기 URL (수정 완료) ---
    path('password_reset/', auth_views.PasswordResetView.as_view(
        # ▼▼▼ [핵심] 모든 template_name에서 'users/'를 삭제합니다. ▼▼▼
        template_name='registration/password_reset.html',
        form_class=CustomPasswordResetForm,
        success_url='/users/password_reset/done/',
        email_template_name='registration/password_reset_email.html'
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html', 
        success_url='/users/reset/done/'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    path('find_id/', views.find_id, name='find_id'),
    
    path('profile/update-stats-visibility/', views.update_stats_visibility, name='update_stats_visibility'),
]
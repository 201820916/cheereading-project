from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect  # 🔹 추가

# 루트(/) 접근 시 로그인 페이지로 리디렉트
def redirect_to_login(request):
    return redirect('/users/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('books/', include('books.urls')),
    path('plans/', include('plans.urls')),
    path('', redirect_to_login),  # 루트 접속 시 로그인으로 이동
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

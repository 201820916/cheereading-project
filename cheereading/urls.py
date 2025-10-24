from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect  # 🔹 필수 import

# 🔹 루트(/) 접근 시 로그인 페이지로 리디렉트
def redirect_to_login(request):
    return redirect('/users/login/')

urlpatterns = [
    path('admin/', admin.site.urls),

    # 앱 URL 포함
    path('users/', include('users.urls')),
    path('books/', include('books.urls')),
    path('plans/', include('plans.urls')),

    # 🔹 루트 접근 시 로그인 페이지로 리디렉트
    path('', redirect_to_login),
]

# 🔹 DEBUG 모드에서 media 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

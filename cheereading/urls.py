from django.contrib import admin
from django.urls import path, include
from django.conf import settings # settings를 import
from django.conf.urls.static import static # static 함수를 import

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ✅ [수정] 이 include가 최상위에 있도록 합니다.
    #    혹시 이 아래에 path('users/', include('django.contrib.auth.urls')) 코드가 있다면 삭제해주세요.
    path('users/', include('users.urls')),
    path('books/', include('books.urls')),
    path('plans/', include('plans.urls')),
    # ... 기타 다른 앱들의 URL ...
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
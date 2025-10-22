from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, Badge, UserBadge

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = '프로필 정보'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

# --- 모델 등록 ---

# User 모델은 CustomUserAdmin으로 한 번만 등록합니다.
admin.site.register(User, CustomUserAdmin)

# Badge와 UserBadge 모델을 등록합니다.
admin.site.register(Badge, BadgeAdmin)
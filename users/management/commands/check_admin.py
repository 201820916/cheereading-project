# users/management/commands/check_admin.py

from django.core.management.base import BaseCommand
from django.contrib import admin
from users.models import UserBadge # UserBadge 모델을 불러옵니다.

class Command(BaseCommand):
    help = '현재 admin 사이트에 어떤 모델들이 등록되어 있는지 확인합니다.'

    def handle(self, *args, **options):
        self.stdout.write("--- Django Admin 등록 상태 검사 시작 ---")
        
        # admin 사이트에 등록된 모든 모델의 목록을 가져옵니다.
        registered_models = admin.site._registry

        self.stdout.write("\n[현재 등록된 모델 목록]")
        for model in registered_models:
            self.stdout.write(f"- {model.__name__}")

        # UserBadge가 등록되어 있는지 직접 확인합니다.
        self.stdout.write("\n[UserBadge 모델 등록 여부 확인]")
        if UserBadge in registered_models:
            self.stdout.write(self.style.SUCCESS("✅ 성공: UserBadge 모델이 admin 사이트에 정상적으로 등록되어 있습니다."))
        else:
            self.stdout.write(self.style.ERROR("❌ 실패: UserBadge 모델이 admin 사이트에 등록되지 않았습니다."))
        
        self.stdout.write("\n--- 검사 완료 ---")
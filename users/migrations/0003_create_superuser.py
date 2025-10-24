import os
from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    """
    Render의 환경 변수를 읽어 관리자 계정을 생성합니다.
    """
    # models.py의 최신 상태가 아닌, 이 시점의 User 모델을 가져옵니다.
    User = get_user_model() 

    ADMIN_USER = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    ADMIN_EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    ADMIN_PASS = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    # 환경 변수가 모두 설정되어 있고, 해당 유저가 없는 경우에만 생성
    if ADMIN_USER and ADMIN_EMAIL and ADMIN_PASS:
        if not User.objects.filter(username=ADMIN_USER).exists():
            print(f"Creating superuser: {ADMIN_USER}")
            User.objects.create_superuser(
                username=ADMIN_USER,
                email=ADMIN_EMAIL,
                password=ADMIN_PASS
            )
        else:
            print(f"Superuser {ADMIN_USER} already exists.")
    else:
        print("Superuser environment variables not set. Skipping superuser creation.")


class Migration(migrations.Migration):

    # 이 마이그레이션이 의존하는 이전 마이그레이션 파일
    # (users 앱의 첫 번째 마이그레이션 파일 이름으로 수정)
    dependencies = [
        ('users', '0001_initial'), # 👈 이 파일 이름이 맞는지 확인!
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
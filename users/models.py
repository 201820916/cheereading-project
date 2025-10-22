# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# ▼▼▼ [수정] User 모델을 명시적으로 정의하고 nickname을 이곳으로 이동 ▼▼▼
class User(AbstractUser):
    # 닉네임은 사용자의 핵심 정보이므로 User 모델에 두는 것이 좋습니다.
    nickname = models.CharField(max_length=150, unique=True, verbose_name='닉네임')

    def __str__(self):
        return self.nickname or self.username

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, verbose_name="자기소개")
    image = models.ImageField(upload_to='profiles/', null=True, blank=True, verbose_name="프로필 이미지")
    age = models.PositiveIntegerField(null=True, blank=True, verbose_name="나이")
    
    # 닉네임 필드는 User 모델로 이동했으므로 여기서 삭제합니다.
    
    GENDER_CHOICES = ( ('M', '남성'), ('F', '여성'), ('O', '기타'), )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, verbose_name="성별")
    
    preferred_genres = models.JSONField(default=list, blank=True, verbose_name="선호 장르 목록")
    preferred_stats = models.JSONField(default=list, blank=True, verbose_name="선호 통계 목록")
    displayed_badges = models.ManyToManyField('Badge', blank=True, related_name="displaying_profiles")

    def __str__(self):
        return f'{self.user.username} Profile'

# User가 생성된 직후(post_save) Profile을 자동으로 생성하는 함수
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

# ▼▼▼ [수정] 불필요하고 위험했던 save_user_profile 시그널과 중복된 시그널을 삭제했습니다. ▼▼▼

class Badge(models.Model):
    name = models.CharField(max_length=100, verbose_name="뱃지 이름")
    description = models.TextField(verbose_name="뱃지 설명")
    icon = models.ImageField(upload_to='badges/', null=True, blank=True)
    def __str__(self):
        return self.name

class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='user_badges'
    )
    badge = models.ForeignKey('Badge', on_delete=models.CASCADE)
    obtained_at = models.DateTimeField(auto_now_add=True)
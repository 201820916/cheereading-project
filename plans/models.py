# plans/models.py

from django.db import models
from django.conf import settings
from books.models import Book

class Plan(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_plans')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True, verbose_name="시작일")
    end_date = models.DateField(null=True, blank=True, verbose_name="종료일")
    target_book_count = models.PositiveIntegerField(default=1, verbose_name="목표 권수")
    
    class Difficulty(models.IntegerChoices):
        VERY_EASY = 1, '⭐'
        EASY = 2, '⭐⭐'
        NORMAL = 3, '⭐⭐⭐'
        HARD = 4, '⭐⭐⭐⭐'
        VERY_HARD = 5, '⭐⭐⭐⭐⭐'

    difficulty = models.IntegerField(choices=Difficulty.choices, default=Difficulty.NORMAL, verbose_name="난이도")
    
    # UserPlan 중간 모델을 통해 User와 관계를 맺습니다.
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='UserPlan', 
        related_name='participating_plans'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# [추가] User와 Plan의 관계 및 상태를 저장하는 중간 모델
class UserPlan(models.Model):
    STATUS_CHOICES = (
        ('participating', '참여 중'),
        ('completed', '완료됨'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='participating')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 한 명의 유저가 동일한 플랜에 중복으로 참여할 수 없도록 설정
        unique_together = ('user', 'plan')

    def __str__(self):
        return f"{self.user.username}'s plan: {self.plan.title} ({self.get_status_display()})"


class PlanBook(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='plan_books')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('plan', 'book')
        ordering = ['order']

    def __str__(self):
        return f"[{self.plan.title}] - {self.book.title}"
    

class UserPlanProgress(models.Model):
    class StatusChoices(models.TextChoices):
        NOT_STARTED = 'not_started', '시작 전'
        IN_PROGRESS = 'in_progress', '독서 중'
        COMPLETED = 'completed', '완료'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NOT_STARTED
    )

    class Meta:
        # 사용자는 한 플랜의 한 책에 대해 하나의 진행 상태만 가질 수 있습니다.
        unique_together = ('user', 'plan', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.plan.title} - {self.book.title}: {self.get_status_display()}"

class PlanFeedback(models.Model):
    """
    사용자가 완료한 플랜에 대한 피드백을 저장하는 모델
    """
    class SatisfactionChoices(models.IntegerChoices):
        VERY_GOOD = 5, '아주 좋았어요'
        GOOD = 4, '좋았어요'
        NORMAL = 3, '보통이에요'
        BAD = 2, '별로였어요'
        VERY_BAD = 1, '아주 별로였어요'

    class DifficultyChoices(models.IntegerChoices):
        EASY = 1, '쉬웠어요'
        PROPER = 2, '적절했어요'
        HARD = 3, '어려웠어요'

    class DurationChoices(models.IntegerChoices):
        SHORT = 1, '짧았어요'
        PROPER = 2, '적절했어요'
        LONG = 3, '길었어요'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plan_feedbacks')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='feedbacks')
    satisfaction = models.IntegerField(choices=SatisfactionChoices.choices, verbose_name="만족도")
    difficulty = models.IntegerField(choices=DifficultyChoices.choices, verbose_name="난이도")
    duration = models.IntegerField(choices=DurationChoices.choices, verbose_name="기간 적절성")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 한 사용자가 하나의 플랜에 대해 한 번만 피드백을 남길 수 있도록 설정
        unique_together = ('user', 'plan')

    def __str__(self):
        return f"{self.user.nickname}'s feedback for '{self.plan.title}'"
    
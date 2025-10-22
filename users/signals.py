# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from books.models import ReadingEntry
from .models import Badge, UserBadge
import datetime # 시간 출력을 위해 추가

def award_badge(user, badge_name):
    """사용자에게 뱃지를 수여하는 함수"""
    print(f"[{datetime.datetime.now()}] ==> 4. award_badge 함수 실행됨. (대상: {user.username}, 뱃지: {badge_name})")
    try:
        badge = Badge.objects.get(name=badge_name)
        print(f"[{datetime.datetime.now()}] ==> 5. DB에서 '{badge_name}' 뱃지 찾기 성공!")
        
        # 뱃지를 획득했는지 확인하고, 결과를 created 변수에 저장
        user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        
        if created:
            print(f"[{datetime.datetime.now()}] ==> 6. ✨ 축하합니다! {user.username}님이 '{badge_name}' 뱃지를 새로 획득했습니다! ✨")
        else:
            print(f"[{datetime.datetime.now()}] ==> 6. {user.username}님은 이 뱃지를 이미 가지고 있습니다.")
            
    except Badge.DoesNotExist:
        print(f"[{datetime.datetime.now()}] ==> 🔴 오류: DB에 '{badge_name}' 이름의 뱃지가 없습니다. 관리자 페이지에서 이름을 정확히 확인해주세요.")

@receiver(post_save, sender=ReadingEntry)
def check_badges_on_read(sender, instance, created, **kwargs):
    """책을 읽은 기록(ReadingEntry)이 저장될 때마다 뱃지 획득 조건을 확인합니다."""
    print(f"\n[{datetime.datetime.now()}] ==> 1. '책 서재 등록' 신호 감지됨! (사용자: {instance.user.username})")
    
    if created: # 새롭게 '읽음' 처리된 경우에만 실행
        print(f"[{datetime.datetime.now()}] ==> 2. '새로운' 등록이므로 뱃지 획득 로직 시작.")
        user = instance.user
        book_count = ReadingEntry.objects.filter(user=user).count()
        print(f"[{datetime.datetime.now()}] ==> 3. 현재까지 등록한 총 책의 수: {book_count}권")

        # --- 뱃지 조건 확인 ---
        if book_count == 1:
            print(f"[{datetime.datetime.now()}] ==> '첫 책 등록!' 뱃지 조건 충족 (책 수: {book_count}권). 뱃지 수여 함수 호출!")
            award_badge(user, '첫 책 등록!')

        if book_count >= 10:
            print(f"[{datetime.datetime.now()}] ==> '열혈 독서가 (10권)' 뱃지 조건 충족 (책 수: {book_count}권). 뱃지 수여 함수 호출!")
            award_badge(user, '열혈 독서가 (10권)')
        
        if book_count >= 50:
            print(f"[{datetime.datetime.now()}] ==> '책벌레 (50권)' 뱃지 조건 충족 (책 수: {book_count}권). 뱃지 수여 함수 호출!")
            award_badge(user, '책벌레 (50권)')
    else:
        print(f"[{datetime.datetime.now()}] ==> 기존 등록 정보를 수정한 것이므로 뱃지 로직을 실행하지 않음.")
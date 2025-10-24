import datetime
import os  # 👈 [추가]
from django.conf import settings  # 👈 [추가]
# import faiss  # [수정] 파일 최상단에서 삭제
# import numpy as np  # [수정] 파일 최상단에서 삭제
# from sentence_transformers import SentenceTransformer  # [수정] 파일 최상단에서 삭제
import json
from django.db.models import Count
from collections import Counter
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from users.models import Profile
from .form import ReadingEntryForm
from .models import Book, ReadingEntry, Wishlist, Genre, UserFeedback
from django.urls import reverse


# --- [수정] 추천 시스템 관련: 지연 로딩(Lazy Loading) ---
REC_MODEL = None
REC_INDEX = None

def load_recommendation_system():
    """추천 시스템 모델과 인덱스를 필요할 때만 로드합니다."""
    global REC_MODEL, REC_INDEX
    
    # 이미 로드되었다면, 다시 로드하지 않음
    if REC_MODEL is not None and REC_INDEX is not None:
        return

    try:
        # [수정] 함수 내부에서 라이브러리를 import 합니다.
        from sentence_transformers import SentenceTransformer
        import faiss
        
        # ▼▼▼ [핵심 수정] FAISS 파일 경로를 BASE_DIR 기준으로 설정 ▼▼▼
        faiss_file_path = os.path.join(settings.BASE_DIR, 'book_index.faiss')

        # 파일 존재 여부 확인
        if not os.path.exists(faiss_file_path):
            print(f"⚠️ ERROR: FAISS file not found at {faiss_file_path}")
            REC_MODEL = None
            REC_INDEX = None
            return
        # ▲▲▲ [핵심 수정] ▲▲▲

        REC_MODEL = SentenceTransformer('jhgan/ko-sroberta-multitask')
        REC_INDEX = faiss.read_index(faiss_file_path) # 👈 수정된 경로 사용
        print("✅ Recommendation model and FAISS index loaded successfully.")

    except FileNotFoundError: # 👈 명시적 에러 처리
        print(f"⚠️ FileNotFoundError: FAISS file not found at {faiss_file_path}")
        REC_MODEL = None
        REC_INDEX = None
    except Exception as e:
        REC_MODEL = None
        REC_INDEX = None
        print(f"⚠️ Error loading recommendation model/index: {e}")
# --- [수정 완료] ---


# --- 기존 뷰 함수들은 변경 없이 그대로 유지됩니다 ---
def home(request):
    """메인 페이지를 렌더링합니다."""
    return render(request, 'home.html')

def book_search(request):
    """책을 검색하고 결과를 페이지네이션하여 보여줍니다."""
    query = request.GET.get('query', '').strip()
    book_list = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query)).distinct() if query else Book.objects.none()
    paginator = Paginator(book_list, 10) 
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'books/book_search.html', context)

def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    
    # --- 기존 리뷰 관련 로직 (변경 없음) ---
    all_reviews = ReadingEntry.objects.filter(book=book).select_related('user').order_by('-read_date')
    user_review = next((r for r in all_reviews if request.user.is_authenticated and r.user.id == request.user.id), None)
    other_reviews = [r for r in all_reviews if r != user_review]
    is_in_library = user_review is not None
    is_in_wishlist = request.user.is_authenticated and not is_in_library and Wishlist.objects.filter(user=request.user, book=book).exists()

    # ▼▼▼ [핵심 추가] 이 책을 읽은 사용자 통계 계산 로직 ▼▼▼
    
    # 1. 이 책을 서재에 추가한 모든 사용자의 프로필을 가져옵니다.
    reader_profiles = Profile.objects.filter(user__readingentry__book=book)
    total_readers = reader_profiles.count()

    # 2. 성별 분포 계산
    gender_distribution = reader_profiles.values('gender').annotate(count=Count('gender')).order_by('-count')
    gender_map = {'M': '남성', 'F': '여성', 'O': '기타'}
    gender_labels = [gender_map.get(item['gender'], '미지정') for item in gender_distribution]
    gender_data = [item['count'] for item in gender_distribution]

    # 3. 연령대 분포 계산
    age_distribution = Counter()
    ages = reader_profiles.filter(age__isnull=False).values_list('age', flat=True)
    for age in ages:
        if age < 20: age_group = '10대'
        elif age < 30: age_group = '20대'
        elif age < 40: age_group = '30대'
        elif age < 50: age_group = '40대'
        else: age_group = '50대 이상'
        age_distribution[age_group] += 1
    
    # 차트 라이브러리에서 사용할 수 있도록 정렬된 데이터로 변환
    age_labels = sorted(age_distribution.keys())
    age_data = [age_distribution[label] for label in age_labels]
    
    # --- 통계 계산 로직 종료 ---

    context = {
        'book': book,
        'is_in_library': is_in_library,
        'user_review': user_review,
        'other_reviews': other_reviews,
        'is_in_wishlist': is_in_wishlist,
        
        # [추가] 템플릿으로 전달할 통계 데이터
        'total_readers': total_readers,
        'gender_labels': json.dumps(gender_labels), # JavaScript에서 사용하기 위해 JSON 문자열로 변환
        'gender_data': json.dumps(gender_data),
        'age_labels': json.dumps(age_labels),
        'age_data': json.dumps(age_data),
    }
    return render(request, 'books/book_detail.html', context)

@login_required
def my_library_view(request):
    """내 서재와 위시리스트를 페이지네이션하여 보여줍니다."""
    reading_entry_list = ReadingEntry.objects.filter(user=request.user).select_related('book').order_by('-read_date')
    paginator_finished = Paginator(reading_entry_list, 6)
    finished_books_page = paginator_finished.get_page(request.GET.get('page_finished'))
    wishlist_item_list = Wishlist.objects.filter(user=request.user).select_related('book').order_by('-created_at')
    paginator_wishlist = Paginator(wishlist_item_list, 5)
    wishlist_items_page = paginator_wishlist.get_page(request.GET.get('page_wishlist'))
    context = {'finished_books_page': finished_books_page, 'wishlist_items_page': wishlist_items_page}
    return render(request, 'books/my_library.html', context)

@login_required
def add_review(request, book_id):
    """책을 서재에 추가하며 리뷰를 작성하는 페이지입니다."""
    book = get_object_or_404(Book, pk=book_id)
    if ReadingEntry.objects.filter(user=request.user, book=book).exists():
        messages.info(request, "이미 리뷰를 작성한 책입니다.")
        return redirect('books:book_detail', book_id=book.id)
    
    if request.method == 'POST':
        form = ReadingEntryForm(request.POST)
        if form.is_valid():

            Wishlist.objects.filter(user=request.user, book=book).delete()

            entry = form.save(commit=False)
            entry.user = request.user
            entry.book = book
            entry.read_date = timezone.now().date()
            entry.save()
            messages.success(request, f"'{book.title}'을(를) 서재에 추가했습니다.")
            return redirect('books:book_detail', book_id=book.id)
    else:
        form = ReadingEntryForm()
    
    context = {'form': form, 'book': book, 'button_text': '서재에 추가 및 리뷰 완료'}
    return render(request, 'books/add_reading_entry.html', context)

@login_required
def add_reading_entry_from_plan(request, book_id):
    """플랜 완료 후, 순차적으로 책을 서재에 등록하는 뷰입니다."""
    # 세션에 플랜 완료 정보가 없으면 비정상 접근으로 처리
    if not request.session.get('plan_completion_flow'):
        messages.error(request, "잘못된 접근입니다.")
        return redirect('plans:my_plans')

    book = get_object_or_404(Book, pk=book_id)

    if request.method == 'POST':
        form = ReadingEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.book = book
            entry.read_date = timezone.now().date()
            entry.save()

            # 처리한 책을 세션의 목록에서 제거
            books_to_process = request.session.get('books_to_process', [])
            if book_id in books_to_process:
                books_to_process.remove(book_id)
                request.session['books_to_process'] = books_to_process

            # 처리할 책이 더 남아있는지 확인
            if books_to_process:
                # 다음 책의 리뷰 작성 페이지로 이동
                next_book_id = books_to_process[0]
                return redirect('books:add_reading_entry_from_plan', book_id=next_book_id)
            else:
                # 모든 책 처리가 끝났을 때
                del request.session['plan_completion_flow']
                messages.success(request, "플랜의 모든 책을 서재에 등록했습니다!")

                # ▼▼▼ [핵심 수정] URL에 GET 파라미터를 추가하는 방식으로 변경 ▼▼▼
                redirect_url = f"{reverse('plans:my_plans')}?tab=completed"
                return redirect(redirect_url)
    else:
        form = ReadingEntryForm()

    context = {'form': form, 'book': book, 'button_text': '다음 책으로'}
    return render(request, 'books/add_reading_entry.html', context)


@login_required
def edit_reading_entry(request, entry_id):
    """리뷰를 수정하는 뷰입니다."""
    entry = get_object_or_404(ReadingEntry, id=entry_id, user=request.user)
    book = entry.book
    if request.method == 'POST':
        form = ReadingEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "리뷰가 성공적으로 수정되었습니다.")
            return redirect('books:book_detail', book_id=book.id)
    else:
        form = ReadingEntryForm(instance=entry)
    context = {'form': form, 'book': book}
    return render(request, 'books/edit_reading_entry.html', context)

@login_required
def add_to_wishlist(request, book_id):
    """책을 위시리스트에 추가합니다."""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        _, created = Wishlist.objects.get_or_create(user=request.user, book=book)
        if created: messages.success(request, f"'{book.title}'을(를) 위시리스트에 추가했습니다.")
        else: messages.info(request, "이미 위시리스트에 있는 책입니다.")
    return redirect(request.META.get('HTTP_REFERER', 'books:search'))

@login_required
def remove_from_wishlist(request, book_id):
    """책을 위시리스트에서 삭제합니다."""
    if request.method == 'POST':
        Wishlist.objects.filter(user=request.user, book_id=book_id).delete()
        messages.success(request, "위시리스트에서 삭제했습니다.")
    return redirect(request.META.get('HTTP_REFERER', 'users:profile'))

@login_required
def delete_reading_entry(request, entry_id):
    """서재에 등록된 책 기록을 삭제합니다."""
    entry = get_object_or_404(ReadingEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        book_title = entry.book.title
        entry.delete()
        messages.success(request, f"'{book_title}' 기록을 서재에서 삭제했습니다.")
    return redirect('books:my_library')

# --- 추천 시스템 핵심 로직 (수정 완료) ---

def _get_recommendations_for_user(user, k=30):
    """사용자의 독서 기록, 피드백, 후보정 필터를 적용하여 책을 추천합니다."""
    
    # [수정] 함수가 호출될 때만 numpy를 import 합니다.
    import numpy as np
    
    # [수정] 함수가 호출될 때 추천 시스템을 로드합니다.
    load_recommendation_system()
    
    if not REC_MODEL or not REC_INDEX:
        return [], "추천 시스템을 준비 중입니다."

    user_entries = ReadingEntry.objects.filter(user=user).select_related('book').prefetch_related('book__genres')
    
    if not user_entries.exists():
        recommendation_type = "선택하신 선호 장르의 인기 도서예요."
        if hasattr(user, 'profile') and hasattr(user.profile, 'get_preferred_genres'):
            preferred_genres = user.profile.get_preferred_genres()
            if preferred_genres:
                recommended_books = list(Book.objects.filter(genres__name__in=preferred_genres).distinct().order_by('?')[:k])
                if recommended_books: return recommended_books, recommendation_type
        return list(Book.objects.all().order_by('?')[:k]), "Cheereading의 인기 추천 도서예요."

    recommendation_type = f"{user.username}님의 독서 기록을 바탕으로 추천하는 책이에요."
    
    weighted_vectors = []
    total_weight = 0
    for entry in user_entries.order_by('-read_date')[:20]:
        if entry.book and entry.book.embedding_vector:
            rating_multiplier = {5: 1.5, 4: 1.2, 3: 1.0, 2: 0.8, 1: 0.5}.get(entry.rating, 1.0)
            book_vector = np.array(entry.book.embedding_vector, dtype=np.float32)
            weighted_vectors.append(book_vector * rating_multiplier)
            total_weight += rating_multiplier
    if not weighted_vectors:
        return list(Book.objects.all().order_by('?')[:k]), "독서 기록을 분석 중입니다. 우선 인기 도서를 추천해드려요."

    user_vector = np.sum(weighted_vectors, axis=0) / total_weight
    user_vector = user_vector.reshape(1, -1).astype('float32')
    
    distances, ids = REC_INDEX.search(user_vector, k * 5) # 후보군 5배로 넉넉하게 확보

    # ▼▼▼ [핵심 1] 사용자 피드백 필터링 (Blocklist) ▼▼▼
    read_book_ids = {entry.book_id for entry in user_entries}
    not_interested_book_ids = set(UserFeedback.objects.filter(user=user, is_interested=False).values_list('book_id', flat=True))
    excluded_ids = read_book_ids.union(not_interested_book_ids)
    
    recommended_ids = [int(book_id) for book_id in ids[0] if int(book_id) not in excluded_ids and int(book_id) != -1]
    
    initial_recommendations = list(Book.objects.filter(id__in=recommended_ids).prefetch_related('genres'))
    initial_recommendations.sort(key=lambda x: recommended_ids.index(x.id))

    # ▼▼▼ [핵심 2] 후보정 필터링 (Gatekeeper) ▼▼▼
    has_read_children_books = user_entries.filter(book__genres__name__in=['아동', '어린이', '유아']).exists()
    final_recommendations = []
    for book in initial_recommendations:
        if not has_read_children_books:
            book_genres = {genre.name for genre in book.genres.all()}
            if '아동' in book_genres or '어린이' in book_genres or '유아' in book_genres:
                continue
        final_recommendations.append(book)
        if len(final_recommendations) >= k:
            break
            
    return final_recommendations, recommendation_type

@login_required
def recommend_books(request):
    """추천된 도서 목록과 위시리스트를 함께 페이지에 렌더링합니다."""
    
    # 1. 기존 추천 로직은 그대로 유지합니다.
    recommended_books, recommendation_type = _get_recommendations_for_user(request.user)
    if not recommended_books:
        recommendation_type = "Cheereading의 인기 추천 도서예요."
        recommended_books = list(Book.objects.all().order_by('?')[:10])

    # ▼▼▼ [핵심 추가] 사용자의 위시리스트를 불러오는 코드 ▼▼▼
    # 최근에 추가한 5개의 항목만 가져옵니다.
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('book').order_by('-created_at')[:5]

    # 2. context에 모든 데이터를 담아 전달합니다.
    context = {
        'recommended_books': recommended_books, 
        'recommendation_type': recommendation_type,
        'wishlist_items': wishlist_items, # [추가] 위시리스트 데이터를 추가
    }
    return render(request, 'books/recommend.html', context)

# ▼▼▼ [핵심 3] 사용자 피드백을 저장하는 API 뷰 추가 ▼▼▼
@login_required
def record_feedback(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        # '관심 없음' 피드백을 찾거나 새로 생성합니다.
        UserFeedback.objects.get_or_create(user=request.user, book=book, defaults={'is_interested': False})
        return JsonResponse({'status': 'success', 'message': '피드백이 기록되었습니다.'})
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)

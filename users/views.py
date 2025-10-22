# users/views.py
import ast
import json
from datetime import timedelta
from collections import Counter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count, Avg
from django.http import JsonResponse
from collections import Counter
from .forms import CustomUserCreationForm, ProfileUpdateForm, NicknameUpdateForm
from .models import Profile, UserBadge, Badge
from books.models import Genre, ReadingEntry, Wishlist
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse # activate 뷰의 반환 타입을 위해 추가
from django.contrib.auth import get_user_model


# --- 내부 헬퍼 함수들 ---

def _get_genre_stats(entries):
    """선호 장르 통계를 계산합니다. 긴 장르 이름은 마지막 부분만 사용합니다."""
    genre_list = []
    for entry in entries:
        for genre in entry.book.genres.all():
            specific_genre = genre.name.split('>')[-1].strip()
            genre_list.append(specific_genre)
            
    genre_counter = Counter(genre_list)
    top_genres = genre_counter.most_common(5)
    
    if top_genres:
        return [g[0] for g in top_genres], [g[1] for g in top_genres]
    return [], []

def _get_monthly_stats(entries):
    """월별 독서량 통계를 계산합니다."""
    today = timezone.now().date()
    first_month = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
    monthly_counts = entries.filter(read_date__gte=first_month).annotate(month=TruncMonth('read_date')).values('month').annotate(count=Count('id')).order_by('month')
    stats_dict = {item['month'].strftime("%Y-%m"): item['count'] for item in monthly_counts}
    
    labels = []
    current_date = today
    for _ in range(12):
        labels.append(current_date.strftime("%Y-%m"))
        current_date = (current_date.replace(day=1) - timedelta(days=1))
    labels.reverse()
    
    data = [stats_dict.get(label, 0) for label in labels]
    return labels, data

def _get_keyword_stats(entries):
    """독서 키워드 통계를 계산합니다. 딕셔너리 형태의 키워드 데이터도 처리하도록 수정합니다."""
    keyword_weights = {}
    for entry in entries:
        if hasattr(entry.book, 'keywords') and entry.book.keywords:
            try:
                # 문자열 데이터를 실제 파이썬 객체(딕셔너리 또는 리스트)로 변환
                keywords_data = ast.literal_eval(entry.book.keywords) if isinstance(entry.book.keywords, str) else entry.book.keywords
                
                # ▼▼▼ [핵심 수정] 데이터가 딕셔너리 형태일 경우를 처리하는 로직 추가 ▼▼▼
                if isinstance(keywords_data, dict):
                    # 딕셔너리의 각 항목(key: value)을 순회하며 가중치를 합산
                    for word, weight in keywords_data.items():
                        keyword_weights[word] = keyword_weights.get(word, 0) + float(weight)

                # 기존의 리스트 형태 데이터도 처리할 수 있도록 유지
                elif isinstance(keywords_data, list):
                    for item in keywords_data:
                        if isinstance(item, dict) and 'word' in item and 'weight' in item:
                            keyword_weights[item['word']] = keyword_weights.get(item['word'], 0) + float(item['weight'])
            
            except (ValueError, SyntaxError, TypeError) as e:
                # 오류가 발생해도 전체가 멈추지 않도록 예외 처리
                print(f"Keyword processing error for book '{entry.book.title}': {e}")
                continue
                
    # 가중치가 높은 순으로 30개만 선택하여 워드클라우드 형식으로 반환
    top_keywords = sorted(keyword_weights.items(), key=lambda x: x[1], reverse=True)[:30]
    return [[word, weight] for word, weight in top_keywords]


def _get_rating_distribution(entries):
    """별점 분포 통계를 계산합니다."""
    rating_counts = {i: 0 for i in range(1, 6)}
    db_counts = entries.values('rating').annotate(count=Count('id'))
    for item in db_counts:
        if item['rating'] in rating_counts:
            rating_counts[item['rating']] = item['count']
    return list(rating_counts.keys()), list(rating_counts.values())

def _get_genre_bias_stats(user):
    """장르별 편향 분석 통계를 계산합니다."""
    genre_stats = Genre.objects.filter(books__readingentry__user=user).annotate(
        avg_rating=Avg('books__readingentry__rating'),
        book_count=Count('books__readingentry', distinct=True)
    ).order_by('-avg_rating')
    analysis_text = ""
    if len(genre_stats) >= 2:
        highest, lowest = genre_stats.first(), genre_stats.last()
        analysis_text = f"회원님은 **{highest.name.split('>')[-1].strip()}** 장르에는 평균 **{highest.avg_rating:.1f}점**의 높은 점수를 주지만, **{lowest.name.split('>')[-1].strip()}** 장르에는 평균 **{lowest.avg_rating:.1f}점**으로 비교적 냉철한 시각을 유지하는군요."
    return genre_stats, analysis_text


def signup(request):
    """회원가입 뷰입니다. 이메일 인증 로직이 추가되었습니다."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 사용자를 생성하지만, 아직 데이터베이스에는 저장하지 않습니다.
            user = form.save(commit=False)
            # 계정을 비활성 상태로 설정합니다.
            user.is_active = False
            user.save()

            # --- 이메일 발송 로직 ---
            current_site = get_current_site(request)
            mail_subject = '[Cheereading] 회원가입 인증 메일입니다.'
            message = render_to_string('users/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            
            # 사용자에게 이메일을 확인하라는 안내 페이지로 리디렉션합니다.
            return redirect('users:signup_done') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

def signup_done(request):
    """회원가입 완료 후 이메일 확인을 안내하는 페이지 뷰입니다."""
    return render(request, 'users/signup_done.html')

def activate(request, uidb64, token):
    """사용자가 이메일의 인증 링크를 클릭했을 때 계정을 활성화하는 뷰입니다."""
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, '계정이 성공적으로 활성화되었습니다! 이제 로그인할 수 있습니다.')
        return redirect('users:login')
    else:
        # 인증이 실패했을 때 보여줄 간단한 메시지
        return HttpResponse('인증 링크가 유효하지 않습니다.', status=400)

@never_cache
@login_required
def profile(request):
    """사용자 프로필 페이지 뷰입니다. 모든 통계 데이터를 계산하고 전달합니다."""
    user = request.user
    profile_obj, _ = Profile.objects.get_or_create(user=user)
    all_reading_entries = ReadingEntry.objects.filter(user=user).order_by('-read_date').select_related('book').prefetch_related('book__genres')

    # 사용자가 설정한 표시 통계 가져오기 (이전 버전 코드 유지)
    preferred_stats = profile_obj.preferred_stats or ['genre', 'monthly', 'rating']

    # 모든 통계 데이터 계산 (헬퍼 함수 호출)
    genre_labels, genre_data = _get_genre_stats(all_reading_entries)
    monthly_labels, monthly_data = _get_monthly_stats(all_reading_entries)
    wordcloud_data = _get_keyword_stats(all_reading_entries)
    rating_labels, rating_data = _get_rating_distribution(all_reading_entries)
    # ▼▼▼ [수정] _get_genre_bias_stats 함수를 호출하여 동적 텍스트 생성 ▼▼▼
    genre_bias_stats, genre_bias_analysis_text = _get_genre_bias_stats(user)

    # 페이지네이션
    paginator_library = Paginator(all_reading_entries, 6)
    reading_entries_page = paginator_library.get_page(request.GET.get('page_library'))
    wishlist_items = Wishlist.objects.filter(user=user).select_related('book').order_by('-created_at')
    paginator_wishlist = Paginator(wishlist_items, 5)
    wishlist_page = paginator_wishlist.get_page(request.GET.get('page_wishlist'))

    # 뱃지 데이터
    displayed_badges = profile_obj.displayed_badges.all()
    user_badges = UserBadge.objects.filter(user=user).select_related('badge').order_by('-obtained_at')

    context = {
        'reading_entries_page': reading_entries_page, 'wishlist_page': wishlist_page,
        'total_books_read': all_reading_entries.count(),
        'genre_labels': genre_labels, 'genre_data': genre_data,
        'monthly_labels': monthly_labels, 'monthly_data': monthly_data,
        'wordcloud_data': wordcloud_data,
        'rating_labels': rating_labels, 'rating_data': rating_data,
        'genre_bias_stats': genre_bias_stats,
        'genre_bias_analysis_text': genre_bias_analysis_text, # 수정된 동적 텍스트 전달
        'displayed_badges': displayed_badges, 'primary_badge': displayed_badges.first(),
        'user_badges': user_badges, 'preferred_stats': preferred_stats,
    }

    return render(request, 'users/profile.html', context)

@login_required
def profile_update(request):
    """프로필과 닉네임을 수정하는 뷰입니다."""
    if request.method == 'POST':
        # ▼▼▼ [수정] 두 개의 폼을 모두 POST 데이터로 초기화합니다. ▼▼▼
        nickname_form = NicknameUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        # ▼▼▼ [수정] 두 폼이 모두 유효한지 확인하고, 모두 저장합니다. ▼▼▼
        if nickname_form.is_valid() and profile_form.is_valid():
            nickname_form.save()
            profile_form.save()
            messages.success(request, '프로필이 성공적으로 수정되었습니다.')
            return redirect('users:profile') # 프로필 페이지로 리디렉션
    else:
        # GET 요청 시, 현재 정보로 폼을 초기화합니다.
        nickname_form = NicknameUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'nickname_form': nickname_form,
        'profile_form': profile_form
    }
    return render(request, 'users/profile_edit.html', context)

# ▼▼▼ [핵심 수정] 템플릿과 통신하는 유일한 API 뷰 ▼▼▼
@login_required
def update_stats_visibility(request):
    """사용자가 선택한 통계 목록을 Profile 모델에 저장하는 API 뷰입니다."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stats_list = data.get('visible_stats', [])
            
            valid_stats = ['genre', 'rating', 'monthly', 'keywords', 'genre_bias']
            
            if all(s in valid_stats for s in stats_list) and len(stats_list) <= 3:
                profile = request.user.profile
                profile.preferred_stats = stats_list
                profile.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': '잘못된 데이터입니다.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '잘못된 JSON 형식입니다.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'POST 요청만 허용됩니다.'}, status=405)

def find_id(request):
    """
    ID 찾기 페이지 뷰입니다.
    POST 요청 시 이메일을 받아 해당 사용자의 아이디(username)를 찾아 보여줍니다.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        User = get_user_model()
        
        try:
            # 입력된 이메일로 사용자를 찾습니다.
            user = User.objects.get(email=email)
            # 사용자를 찾으면, 아이디를 메시지와 함께 다시 템플릿에 전달합니다.
            context = {'found_username': user.username}
            return render(request, 'users/find_id_result.html', context)
        except User.DoesNotExist:
            # 해당 이메일의 사용자가 없으면 오류 메시지를 전달합니다.
            messages.error(request, '해당 이메일로 가입된 아이디가 없습니다.')
            return render(request, 'users/find_id.html') # 다시 ID 찾기 폼을 보여줍니다.
        except Exception as e:
            # 기타 예상치 못한 오류 처리
            messages.error(request, f'오류가 발생했습니다: {e}')
            return render(request, 'users/find_id.html')

    # GET 요청 시에는 그냥 ID 찾기 폼을 보여줍니다.
    return render(request, 'users/find_id.html')

def _get_genre_bias_stats(user):
    """ 사용자의 장르별 독서 통계 및 편향 분석 텍스트를 반환합니다. """
    genre_bias_stats = []
    genre_bias_analysis_text = "독서 기록이 부족하여 장르 편향을 분석할 수 없습니다."
    
    # 사용자가 읽은 모든 책 기록을 가져옵니다 (장르 정보 포함).
    user_entries = ReadingEntry.objects.filter(user=user).select_related('book').prefetch_related('book__genres')
    total_books_read = user_entries.count()

    if total_books_read >= 3: # 최소 3권 이상 읽었을 때만 분석
        genre_ratings = {} # { '장르명': [별점 리스트], ... }
        genre_counts = Counter() # { '장르명': 읽은 권수, ... }

        # 각 독서 기록을 순회하며 장르별 별점과 권수를 집계합니다.
        for entry in user_entries:
            if entry.rating is not None: # 별점이 있는 기록만 집계
                for genre in entry.book.genres.all():
                    # 장르 이름에서 마지막 부분만 사용 (예: '소설 > 한국소설' -> '한국소설')
                    specific_genre = genre.name.split('>')[-1].strip()
                    if specific_genre:
                        if specific_genre not in genre_ratings:
                            genre_ratings[specific_genre] = []
                        genre_ratings[specific_genre].append(entry.rating)
                        genre_counts[specific_genre] += 1
        
        # 평균 별점 계산
        calculated_stats = []
        for genre, ratings in genre_ratings.items():
            if ratings: # 별점 기록이 있는 경우만
                avg_rating = sum(ratings) / len(ratings)
                calculated_stats.append({
                    'name': genre,
                    'book_count': genre_counts[genre],
                    'avg_rating': avg_rating
                })
        
        # 평균 별점 높은 순으로 정렬
        genre_bias_stats = sorted(calculated_stats, key=lambda x: x['avg_rating'], reverse=True)

        # 동적 문구 생성 로직 (기존과 동일)
        if len(genre_bias_stats) >= 2:
            highest = genre_bias_stats[0]
            lowest = genre_bias_stats[-1]

            if highest['avg_rating'] > lowest['avg_rating'] + 1:
                genre_bias_analysis_text = (
                    f"회원님은 **{highest['name']}** 장르에 평균 **{highest['avg_rating']:.1f}점**의 높은 점수를 주시는 반면, "
                    f"**{lowest['name']}** 장르에는 평균 **{lowest['avg_rating']:.1f}점**으로 비교적 관심도가 낮으신 편입니다."
                )
            elif len(genre_bias_stats) > 3:
                 genre_bias_analysis_text = f"**{highest['name']}** 장르를 포함하여 다양한 분야의 책을 즐겨 읽으시는군요! "
                 genre_bias_analysis_text += f"가장 높은 평점을 주신 장르는 평균 **{highest['avg_rating']:.1f}점**입니다."
            else:
                genre_bias_analysis_text = f"여러 장르의 책을 비교적 고르게 읽고 계십니다. 그중 **{highest['name']}** 장르에 가장 높은 평균 점수(**{highest['avg_rating']:.1f}점**)를 주셨네요."

        elif len(genre_bias_stats) == 1:
            single = genre_bias_stats[0]
            genre_bias_analysis_text = f"주로 **{single['name']}** 장르의 책을 읽으셨군요! 이 장르에 평균 **{single['avg_rating']:.1f}점**을 주셨습니다."

    return genre_bias_stats, genre_bias_analysis_text
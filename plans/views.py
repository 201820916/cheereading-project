# plans/views.py

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Plan, PlanBook, UserPlan, UserPlanProgress
from .forms import PlanCreateForm, PlanForm
from books.models import Book, ReadingEntry
from django.db.models import Q
import json
from django.views.decorators.http import require_POST
from .models import Plan, PlanBook, PlanBook, UserPlan, UserPlanProgress, PlanFeedback # PlanFeedback 추가
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, F, FloatField
from django.db.models.functions import Cast


@login_required
def plan_list(request):
    all_public_plans = Plan.objects.all().order_by('-created_at')
    selected_plan_id = request.GET.get('plan_id')
    selected_plan = None
    aggregated_feedback = {} # 통계 변수 초기화

    if selected_plan_id:
        selected_plan = all_public_plans.filter(id=selected_plan_id).first()
        if selected_plan: # selected_plan이 실제로 존재할 때만 계산
            aggregated_feedback = calculate_feedback_stats(selected_plan) # 헬퍼 함수 호출
    elif all_public_plans.exists():
        selected_plan = all_public_plans.first()
        aggregated_feedback = calculate_feedback_stats(selected_plan) # 헬퍼 함수 호출

    context = {
        'all_plans': all_public_plans,
        'selected_plan': selected_plan,
        'aggregated_feedback': aggregated_feedback, # context에 추가
    }
    return render(request, 'plans/plan_list.html', context)

@login_required
def plan_detail(request, plan_id):
    plan = get_object_or_404(Plan.objects.prefetch_related('plan_books__book', 'participants'), id=plan_id)
    aggregated_feedback = calculate_feedback_stats(plan)

    context = {
        'plan': plan,
        'aggregated_feedback': aggregated_feedback, # context에 추가
    }
    return render(request, 'plans/plan_detail.html', context)
    

@login_required
def plan_create(request):
    if request.method == 'POST':
        form = PlanCreateForm(request.POST)
        # form.is_valid()가 호출될 때 위에서 작성한 clean 메서드가 실행됩니다.
        if form.is_valid():
            # 폼 검증이 성공했으므로, 목표 권수와 실제 선택 수가 일치함이 보장됩니다.
            plan = form.save(commit=False)
            plan.creator = request.user
            plan.save() # 먼저 플랜 객체를 저장해야 ID가 생성됩니다.

            # 숨겨진 필드에서 책 ID 목록을 가져와 PlanBook 객체를 생성합니다.
            selected_books_str = request.POST.get('selected_books', '')
            if selected_books_str:
                book_ids = [int(book_id) for book_id in selected_books_str.split(',') if book_id]
                
                # PlanBook 객체를 한 번에 여러 개 생성 (Bulk Create)
                plan_books = [PlanBook(plan=plan, book_id=book_id) for book_id in book_ids]
                PlanBook.objects.bulk_create(plan_books)

            messages.success(request, '새로운 독서 플랜이 생성되었습니다.')
            return redirect('plans:my_plans') # 플랜 목록 페이지 등으로 리디렉션
    else:
        form = PlanCreateForm()

    context = {'form': form}
    return render(request, 'plans/plan_form.html', context)


@login_required
def plan_update(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, creator=request.user)
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            updated_plan = form.save()
            PlanBook.objects.filter(plan=updated_plan).delete()
            selected_book_ids = request.POST.getlist('books')
            for index, book_id in enumerate(selected_book_ids):
                book = get_object_or_404(Book, id=book_id)
                PlanBook.objects.create(plan=updated_plan, book=book, order=index + 1)
            messages.success(request, "계획이 성공적으로 수정되었습니다.")
            return redirect(f"{reverse('plans:plan_list')}?plan_id={plan.id}")
    else:
        form = PlanForm(instance=plan)
    return render(request, 'plans/plan_form.html', {'form': form, 'plan': plan})

@login_required
def plan_delete(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, creator=request.user)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, "계획을 삭제했습니다.")
    return redirect('plans:plan_list')

@login_required
def remove_book_from_plan(request, plan_id, book_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if plan.creator != request.user:
        messages.error(request, "본인이 생성한 계획만 수정할 수 있습니다.")
        return redirect('plans:plan_detail', plan_id=plan.id)
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        plan_book = PlanBook.objects.filter(plan=plan, book=book)
        if plan_book.exists():
            plan_book.delete()
            messages.success(request, f"'{book.title}' 책을 계획에서 제거했습니다.")
    return redirect('plans:plan_detail', plan_id=plan.id)

@login_required
def my_plans(request):
    active_tab = request.GET.get('tab', 'participating')
    user = request.user

    # --- 탭별 플랜 목록 가져오기 ---
    participating_user_plans = UserPlan.objects.filter(user=user, status='participating').select_related('plan').exclude(plan__creator=user)
    created_plans = Plan.objects.filter(creator=user).prefetch_related('plan_books__book')
    completed_plans = UserPlan.objects.filter(user=user, status='completed').select_related('plan')

    # --- 변수 초기화 ---
    selected_plan_id = request.GET.get('plan_id')
    selected_plan = None
    books_for_display = []
    all_books_completed = False
    user_feedback_exists = False
    aggregated_feedback = {}  # (추가) 집계된 피드백을 담을 딕셔너리

    if selected_plan_id:
        selected_plan = get_object_or_404(Plan.objects.prefetch_related('plan_books__book'), id=selected_plan_id)
        books_for_display = list(selected_plan.plan_books.all())

        # --- 탭에 따른 로직 분기 ---
        if active_tab == 'participating':
            progress_objects = UserPlanProgress.objects.filter(user=user, plan=selected_plan)
            user_progresses = {p.book_id: p.status for p in progress_objects}

            for plan_book in books_for_display:
                plan_book.current_status = user_progresses.get(plan_book.book.id, UserPlanProgress.StatusChoices.NOT_STARTED)

            completed_count = list(user_progresses.values()).count(UserPlanProgress.StatusChoices.COMPLETED)
            if len(books_for_display) > 0 and len(books_for_display) == completed_count:
                all_books_completed = True

        elif active_tab == 'completed':
            user_feedback_exists = PlanFeedback.objects.filter(user=user, plan=selected_plan).exists()

            # ▼▼▼ [핵심 추가] 피드백 집계 로직 ▼▼▼
            all_feedback_for_plan = PlanFeedback.objects.filter(plan=selected_plan)
            if all_feedback_for_plan.exists():
                # 1. 만족도(satisfaction) 최빈값 계산
                most_common_satisfaction = all_feedback_for_plan.values('satisfaction').annotate(count=Count('satisfaction')).order_by('-count').first()
                if most_common_satisfaction:
                    satisfaction_map = dict(PlanFeedback.SatisfactionChoices.choices)
                    aggregated_feedback['satisfaction'] = satisfaction_map.get(most_common_satisfaction['satisfaction'])

                # 2. 난이도(difficulty) 최빈값 계산
                most_common_difficulty = all_feedback_for_plan.values('difficulty').annotate(count=Count('difficulty')).order_by('-count').first()
                if most_common_difficulty:
                    difficulty_map = dict(PlanFeedback.DifficultyChoices.choices)
                    aggregated_feedback['difficulty'] = difficulty_map.get(most_common_difficulty['difficulty'])

                # 3. 기간(duration) 최빈값 계산
                most_common_duration = all_feedback_for_plan.values('duration').annotate(count=Count('duration')).order_by('-count').first()
                if most_common_duration:
                    duration_map = dict(PlanFeedback.DurationChoices.choices)
                    aggregated_feedback['duration'] = duration_map.get(most_common_duration['duration'])
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    # --- 템플릿으로 전달할 최종 데이터 ---
    context = {
        'active_tab': active_tab,
        'participating_user_plans': participating_user_plans,
        'created_plans': created_plans,
        'completed_plans': completed_plans,
        'selected_plan': selected_plan,
        'books_for_display': books_for_display,
        'status_choices': UserPlanProgress.StatusChoices.choices,
        'all_books_completed': all_books_completed,
        'user_feedback_exists': user_feedback_exists,
        'aggregated_feedback': aggregated_feedback,  # (추가) 집계된 피드백 전달
    }
    return render(request, 'plans/my_plans.html', context)

@login_required
def toggle_bookmark(request, plan_id):
    if request.method == 'POST':
        plan = get_object_or_404(Plan, id=plan_id)
        user = request.user
        if plan.creator == user:
            messages.warning(request, "자신이 만든 플랜은 북마크할 수 없습니다.")
        else:
            user_plan, created = UserPlan.objects.get_or_create(user=user, plan=plan)
            if not created:
                user_plan.delete()
                messages.success(request, f"'{plan.title}' 플랜을 북마크에서 제거했습니다.")
            else:
                messages.success(request, f"'{plan.title}' 플랜을 북마크했습니다.")
    return redirect(request.META.get('HTTP_REFERER', 'plans:plan_list'))

@login_required
def toggle_book_progress(request, plan_book_id):
    if request.method == 'POST':
        plan_book = get_object_or_404(PlanBook, id=plan_book_id)
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            progress, _ = UserPlanProgress.objects.update_or_create(
                user=request.user, plan_book=plan_book,
                defaults={'status': new_status}
            )
            return JsonResponse({'status': 'success', 'new_status': progress.status})
        except:
            return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)

@require_POST
@login_required
def complete_plan(request, plan_id):
    """플랜을 완료 처리하고, 서재 등록 절차를 시작합니다."""
    user_plan = get_object_or_404(UserPlan, user=request.user, plan_id=plan_id)
    plan = user_plan.plan

    # 1. UserPlan 상태를 'completed'로 변경
    user_plan.status = 'completed'
    user_plan.save()

    # 2. 서재에 등록할 책 목록을 세션에 저장 (이미 서재에 있는 책은 제외)
    plan_book_ids = list(plan.plan_books.values_list('book_id', flat=True))
    existing_library_book_ids = list(ReadingEntry.objects.filter(
        user=request.user, book_id__in=plan_book_ids
    ).values_list('book_id', flat=True))
    
    books_to_process = [bid for bid in plan_book_ids if bid not in existing_library_book_ids]

    if not books_to_process:
        messages.success(request, f"'{plan.title}' 플랜을 완료했습니다! 모든 책이 이미 서재에 있습니다.")
        return redirect('plans:my_plans', tab='completed')

    # 3. 세션에 정보를 저장하고 서재 등록(리뷰 작성) 첫 페이지로 이동
    request.session['plan_completion_flow'] = True
    request.session['books_to_process'] = books_to_process
    
    messages.info(request, f"'{plan.title}' 플랜을 완료했습니다. 이제 각 책에 대한 리뷰를 작성해주세요.")
    
    first_book_id = books_to_process[0]
    return redirect('books:add_reading_entry_from_plan', book_id=first_book_id)

def book_search_api(request):
    query = request.GET.get('query', '')
    books_data = []
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct()[:50]
        for book in books:
            books_data.append({'id': book.id, 'title': book.title, 'author': book.author})
    return JsonResponse({'books': books_data})

@login_required
def save_plan_feedback(request, plan_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan = get_object_or_404(Plan, id=plan_id)

            PlanFeedback.objects.update_or_create(
                user=request.user,
                plan=plan,
                defaults={
                    'satisfaction': data.get('satisfaction'),
                    # ▼▼▼ [수정] 필드 이름을 모델과 일치시킵니다. ▼▼▼
                    'difficulty': data.get('difficulty'),
                    'duration': data.get('duration'),
                }
            )
            return JsonResponse({'status': 'success'})
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'status': 'error', 'message': '잘못된 데이터입니다.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'POST 요청만 허용됩니다.'}, status=405)

@require_POST
@login_required
def update_plan_progress(request, plan_id, book_id):
    """(AJAX) 사용자의 플랜 도서 진행 상태를 업데이트합니다."""
    new_status = request.POST.get('status')

    # 전달받은 status 값이 유효한지 확인합니다.
    if new_status not in UserPlanProgress.StatusChoices.values:
        return JsonResponse({'status': 'error', 'message': '유효하지 않은 상태입니다.'}, status=400)

    # UserPlanProgress 객체를 찾거나 새로 생성하여 상태를 업데이트합니다.
    progress, created = UserPlanProgress.objects.update_or_create(
        user=request.user,
        plan_id=plan_id,
        book_id=book_id,
        defaults={'status': new_status}
    )
    return JsonResponse({'status': 'success', 'message': '진행 상태가 업데이트되었습니다.'})

def calculate_feedback_stats(plan):
    """주어진 플랜에 대한 피드백 통계(최빈값 및 비율)를 계산합니다."""
    aggregated_feedback = {}
    all_feedback_for_plan = PlanFeedback.objects.filter(plan=plan)
    total_feedback_count = all_feedback_for_plan.count()

    if total_feedback_count > 0:
        # 각 필드별로 최빈값과 비율 계산
        for field, choices in [
            ('satisfaction', PlanFeedback.SatisfactionChoices),
            ('difficulty', PlanFeedback.DifficultyChoices),
            ('duration', PlanFeedback.DurationChoices)
        ]:
            most_common = all_feedback_for_plan.values(field)\
                            .annotate(count=Count(field))\
                            .order_by('-count')\
                            .first()
            if most_common:
                choice_map = dict(choices.choices)
                mode_value = most_common[field]
                mode_count = most_common['count']
                percentage = round((mode_count / total_feedback_count) * 100)
                aggregated_feedback[field] = {
                    'text': choice_map.get(mode_value),
                    'percentage': percentage,
                }
    return aggregated_feedback
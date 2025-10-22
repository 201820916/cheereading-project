# plans/forms.py
from django import forms
from .models import Plan

class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        # ✅ 'difficulty'를 포함한 다른 필드들을 추가합니다.
        fields = [
            'title', 
            'description', 
            'start_date', 
            'end_date', 
            'target_book_count', 
            'difficulty'
        ]
        
        # ✅ 사용자 경험 향상을 위해 위젯을 설정합니다.
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

# plans/forms.py

from django import forms
from .models import Plan

class PlanCreateForm(forms.ModelForm):
    selected_books = forms.CharField(widget=forms.HiddenInput(), required=False)
    difficulty = forms.IntegerField(widget=forms.HiddenInput(), initial=1, required=False)

    class Meta:
        model = Plan
        fields = [
            'title',
            'description',
            'start_date',
            'end_date',
            # ▼▼▼ [수정] 필드 이름을 'target_book_count'로 변경합니다. ▼▼▼
            'target_book_count',
            'difficulty'
        ]
        labels = {
            'title': '플랜 제목',
            'description': '플랜 설명',
            # ▼▼▼ [수정] 라벨 키도 'target_book_count'로 변경합니다. ▼▼▼
            'target_book_count': '목표 권수',
            'start_date': '시작일',
            'end_date': '종료일',
            'difficulty': '난이도',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # ▼▼▼ [수정] cleaned_data에서 가져오는 필드 이름도 'target_book_count'로 변경합니다. ▼▼▼
        target_books_count = cleaned_data.get('target_book_count')
        selected_books_str = self.data.get('selected_books', '')

        if selected_books_str:
            actual_books_count = len([book_id for book_id in selected_books_str.split(',') if book_id])
        else:
            actual_books_count = 0

        if target_books_count is not None and actual_books_count != target_books_count:
            raise forms.ValidationError(
                f"목표 권수({target_books_count}권)와 선택한 책의 수({actual_books_count}권)가 일치하지 않습니다. 책을 다시 선택해주세요."
            )

        return cleaned_data
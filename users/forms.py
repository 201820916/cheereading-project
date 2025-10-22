# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, AuthenticationForm
from .models import User, Profile
from django import forms
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

# --- 선택 목록 (재사용을 위해 한 곳에 정리) ---
GENRE_CHOICES = [
    ('', '장르 선택'), ('소설', '소설'), ('시/에세이', '시/에세이'), 
    ('인문', '인문'), ('역사', '역사'), ('과학', '과학'),
    ('경제/경영', '경제/경영'), ('자기계발', '자기계발'), ('여행', '여행'),
]

GENDER_CHOICES = (
    ('', '성별 선택'), ('M', '남성'), ('F', '여성'), ('O', '기타'),
)

# --- 회원가입 폼 (대대적 수정) ---
class CustomUserCreationForm(UserCreationForm):
    # ▼▼▼ 1. 닉네임, 프로필 관련 필드를 명확하게 정의합니다. ▼▼▼
    nickname = forms.CharField(label="닉네임", required=True)
    email = forms.EmailField(label="이메일 주소", required=True)
    age = forms.IntegerField(label="나이", required=True)
    gender = forms.ChoiceField(label="성별", choices=GENDER_CHOICES, required=True)
    preferred_genre_1 = forms.ChoiceField(label="선호 장르 1", choices=GENRE_CHOICES, required=True)
    preferred_genre_2 = forms.ChoiceField(label="선호 장르 2", choices=GENRE_CHOICES, required=True)
    preferred_genre_3 = forms.ChoiceField(label="선호 장르 3", choices=GENRE_CHOICES, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        # User 모델에 저장할 필드들을 지정합니다. (ID, 닉네임, 이메일)
        fields = ('username', 'nickname', 'email')

    # ▼▼▼ 2. [핵심] 모든 필드에 Bootstrap 클래스를 자동으로 추가하는 로직 ▼▼▼
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # username의 라벨을 '아이디'로 변경
        self.fields['username'].label = '아이디'

        # 모든 필드 위젯에 'form-control' 클래스를 추가하여 디자인이 깨지지 않게 합니다.
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        # super().save()는 User 객체를 생성하고 반환합니다.
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Profile 객체를 생성하거나 가져와서 추가 정보를 저장합니다.
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'age': self.cleaned_data.get('age'),
                    'gender': self.cleaned_data.get('gender'),
                    'preferred_genre_1': self.cleaned_data.get('preferred_genre_1'),
                    'preferred_genre_2': self.cleaned_data.get('preferred_genre_2'),
                    'preferred_genre_3': self.cleaned_data.get('preferred_genre_3'),
                }
            )
        return user

# --- 프로필 수정 폼 ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'image']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class NicknameUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        # ▼▼▼ [수정] fields를 'username'에서 'nickname'으로 변경합니다. ▼▼▼
        fields = ['nickname']
        # ▼▼▼ [수정] labels도 'nickname'으로 변경합니다. ▼▼▼
        labels = {
            'nickname': '닉네임',
        }
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
        }

# --- 비밀번호 재설정 폼 ---
class CustomPasswordResetForm(PasswordResetForm):
    # 아이디 입력 필드 추가
    username = forms.CharField(label=_("아이디"), max_length=150)

    # 기존 email 필드는 유지
    
    def clean(self):
        """아이디와 이메일이 일치하는지 검증합니다."""
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        
        if email and username:
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                if user.email != email:
                    raise forms.ValidationError(
                        _("입력하신 아이디와 이메일 정보가 일치하지 않습니다."),
                        code='email_mismatch',
                    )
            except User.DoesNotExist:
                raise forms.ValidationError(
                    _("입력하신 아이디를 찾을 수 없습니다."),
                    code='username_not_found',
                )
        return cleaned_data

    def get_users(self, email):
        """아이디를 기준으로 사용자를 찾도록 재정의합니다."""
        User = get_user_model()
        username = self.cleaned_data.get('username')
        if username:
            active_users = User._default_manager.filter(**{
                '%s__iexact' % User.USERNAME_FIELD: username,
                'is_active': True,
            })
            return (u for u in active_users)
        # 아이디가 없으면 (일반적이지 않음) 빈 쿼리셋 반환
        return User.objects.none()

# --- 커스텀 로그인 폼 (기존 코드 유지) ---
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control', 'placeholder': '아이디'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control', 'placeholder': '비밀번호'
        })
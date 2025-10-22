# books/forms.py

from django import forms
from .models import ReadingEntry
import unicodedata

class ReadingEntryForm(forms.ModelForm):
    class Meta:
        model = ReadingEntry
        fields = ['rating', 'review', 'detailed_review']
        widgets = {
            'rating': forms.NumberInput(attrs={'type': 'hidden', 'id': 'id_rating'}),
            'review': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': '100자 평은 필수입니다.'
            }),
            'detailed_review': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10, 
                'placeholder': '여기에 상세 리뷰를 남겨주세요 (선택 사항)'
            }),
        }
        labels = {
            'review': '100자평',
            'detailed_review': '상세평',
        }

    def clean_review(self):
        """
        자음/모음 비율을 분석하여 무의미한 리뷰를 필터링합니다.
        - 소리 없는 초성 'ㅇ'은 자음 계산에서 제외합니다.
        - ㄺ, ㅄ 등 복잡한 받침을 정확하게 계산합니다.
        - 필터링 기준을 완화하여 정상적인 문장이 차단될 확률을 낮춥니다.
        """
        review_text = self.cleaned_data.get('review', '')

        # 한글이 아닌 문자는 필터링에서 제외
        korean_text = "".join(filter(lambda char: '가' <= char <= '힣', review_text))
        if not korean_text:
            return review_text # 검사할 한글이 없으면 통과

        # 각 받침을 구성 자음으로 분해하기 위한 맵
        JONG_DECOMPOSITION_MAP = {
            '': 0, 'ㄱ': 1, 'ㄲ': 1, 'ㄳ': 2, 'ㄴ': 1, 'ㄵ': 2, 'ㄶ': 2, 'ㄷ': 1, 'ㄹ': 1, 
            'ㄺ': 2, 'ㄻ': 2, 'ㄼ': 2, 'ㄽ': 2, 'ㄾ': 2, 'ㄿ': 2, 'ㅀ': 2, 'ㅁ': 1, 'ㅂ': 1, 
            'ㅄ': 2, 'ㅅ': 1, 'ㅆ': 1, 'ㅇ': 1, 'ㅈ': 1, 'ㅊ': 1, 'ㅋ': 1, 'ㅌ': 1, 'ㅍ': 1, 'ㅎ': 1
        }
        JONGSUNG_LIST = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        consonant_count = 0
        vowel_count = 0

        for char in korean_text:
            char_code = ord(char) - ord('가')
            
            # 1. 초성 계산 (소리 없는 'ㅇ'은 제외)
            chosung_index = char_code // (21 * 28)
            if chosung_index != 11:  # 초성 'ㅇ'의 인덱스는 11
                consonant_count += 1
            
            # 2. 중성 계산 (모두 모음)
            vowel_count += 1
            
            # 3. 종성 계산 (복잡한 받침도 정확히 카운트)
            jongsung_index = char_code % 28
            if jongsung_index > 0:
                jongsung_char = JONGSUNG_LIST[jongsung_index]
                consonant_count += JONG_DECOMPOSITION_MAP.get(jongsung_char, 0)
        
        total_count = consonant_count + vowel_count

        if total_count > 0:
            consonant_ratio = (consonant_count / total_count) * 100
            vowel_ratio = (vowel_count / total_count) * 100
            
            # ▼▼▼ [수정] 필터링 기준을 더 너그럽게 변경 ▼▼▼
            # 자음 비율이 40% 미만 또는 65% 초과일 때 필터링
            if consonant_ratio > 65 or consonant_ratio < 40:
                raise forms.ValidationError(
                    "리뷰 내용이 올바르지 않습니다. 자음 또는 모음의 비율이 비정상적입니다. (예: 'ㅋㅋㅋㅋ', 'ㅠㅠㅠ')"
                )
        
        return review_text
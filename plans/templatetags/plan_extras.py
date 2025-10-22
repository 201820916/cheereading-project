# plans/templatetags/plan_extras.py

from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    템플릿에서 딕셔너리의 값을 변수 키로 가져올 수 있게 해주는 필터입니다.
    사용법: {{ my_dictionary|get_item:my_variable }}
    """
    return dictionary.get(key)
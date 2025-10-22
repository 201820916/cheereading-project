# plans/admin.py

from django.contrib import admin
from .models import Plan, PlanBook

admin.site.register(Plan)
admin.site.register(PlanBook)
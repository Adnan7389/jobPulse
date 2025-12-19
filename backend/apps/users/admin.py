from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'telegram_id', 'experience_level', 'years_experience')
    list_filter = ('experience_level',)
    search_fields = ('username', 'bio')
    fieldsets = (
        ('Basic Info', {'fields': ('username', 'telegram_id')}),
        ('Skills & Experience', {'fields': ('skills', 'job_titles', 'experience_level', 'years_experience', 'bio')}),
        ('Preferences', {'fields': ('preferences',)}),
    )

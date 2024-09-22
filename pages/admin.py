from django.contrib import admin

from pages.models import About


# Register your models here.
@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'created', 'last')
    ordering = ('position',)
    search_fields = ('title', 'description')

from django.contrib import admin
from .models import ContextoPrompt

@admin.register(ContextoPrompt)
class ContextoPromptAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_editable = ("activo",)
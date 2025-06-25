from django.contrib import admin
from .models import ContextoPrompt, DatosFuenteMensaje

admin.site.register(DatosFuenteMensaje)

@admin.register(ContextoPrompt)
class ContextoPromptAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_editable = ("activo",)
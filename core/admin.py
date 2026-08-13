from django.contrib import admin
from .models import ImpresoraFiscal

@admin.register(ImpresoraFiscal)
class ImpresoraFiscalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'serial', 'activa')
    list_editable = ('activa',)
    search_fields = ('nombre', 'serial')

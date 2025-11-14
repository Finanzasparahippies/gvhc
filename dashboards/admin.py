from django.contrib import admin
from django.utils.html import format_html
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_at', 'created_at', 'image_tag')
    list_filter = ('source', 'published_at', 'created_at')
    search_fields = ('title', 'summary', 'source')
    ordering = ('-published_at',)
    readonly_fields = ('created_at',)

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="object-fit:contain;" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Imagen'

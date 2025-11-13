from rest_framework import serializers
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ['id', 'title', 'summary', 'url', 'published_at', 'source', 'created_at', 'level', 'image']

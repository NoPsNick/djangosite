from rest_framework import serializers
from legaldocs.models import TermOfService


class TermOfServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermOfService
        fields = [
            'title',
            'content'
        ]

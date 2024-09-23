from rest_framework import serializers

from legaldocs.models import TermOfService, PrivacyPolicy, ReturnPolicy


class TermOfServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermOfService
        fields = [
            'title',
            'content',
            'modified'
        ]


class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = [
            'title',
            'content',
            'modified'
        ]


class ReturnPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnPolicy
        fields = [
            'title',
            'content',
            'modified'
        ]

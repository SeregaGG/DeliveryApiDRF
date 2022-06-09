from rest_framework import serializers
from .models import Contact, Deal


class ContactSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        return Contact(**self.validated_data)

    class Meta:
        model = Contact
        fields = '__all__'


class DealSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        return Deal(**self.validated_data)

    class Meta:
        model = Deal
        fields = '__all__'



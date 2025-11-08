from rest_framework import serializers
import re
from .models import LandingMediaFile

PHONE_PATTERN = re.compile(r'^0\d{10}$')

class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11, min_length=11)

    def validate_phone(self, value):
        if not PHONE_PATTERN.match(value):
            raise serializers.ValidationError(
                "شماره موبایل باید با 0 شروع شود و دقیقاً ۱۱ رقم باشد."
            )
        return value

class LandingMediaFileSerializer(serializers.ModelSerializer):
    file_type = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    is_video = serializers.BooleanField(read_only=True)

    class Meta:
        model = LandingMediaFile
        fields = ["title", "file", "file_type", "is_image", "is_video"]

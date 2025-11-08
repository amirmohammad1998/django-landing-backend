from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PhoneSerializer, LandingMediaFileSerializer
from .tasks import save_phone_async
from .models import LandingMediaFile
from rest_framework.throttling import AnonRateThrottle
import uuid

class RegisterPhoneView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        user_agent = request.META.get("HTTP_USER_AGENT")
        referrer = request.META.get("HTTP_REFERER")
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        save_phone_async.delay(
            phone=phone,
            ip=ip,
            user_agent=user_agent,
            referrer=referrer,
            request_id=request_id,
        )

        response = Response(
            {"detail": "شماره شما با موفقیت ثبت شد."},
            status=status.HTTP_202_ACCEPTED,
        )
        response["Cache-Control"] = "no-store"
        return response


class LandingMediaView(APIView):
    """
    Returns the default media (image or video) for the landing page.
    If no default file is marked, returns null values.
    """

    def get(self, request):
        media = LandingMediaFile.objects.filter(is_default=True).first()
        if media:
            serializer = LandingMediaFileSerializer(media)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {'message': 'There is no uploaded media file or selected as default.'},
            status=status.HTTP_204_NO_CONTENT
        )
from django.dispatch import receiver
from landing.models import LandingMediaFile
from django.db.models.signals import post_save
from django.db import transaction

@receiver(post_save, sender=LandingMediaFile)
def update_default_landing_media_files(sender, instance, created, **kwargs):
    # Only this one is default. update other one's default = False
    if instance.is_default:
        with transaction.atomic():
            # Find previous record with default = true. Exclude current instance
            previous_default = (
                sender.objects.filter(is_default=True)
                .exclude(pk=instance.pk)
                .first()
            )

            # If is_default = True found, update it to is_default = False
            if previous_default:
                previous_default.is_default = False
                previous_default.save(update_fields=["is_default"])

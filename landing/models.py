from django.db import models
import mimetypes

class LandingMediaFile(models.Model):
    """
        We have a file in landing page that is the only one. It is passible that is image or video.
        Here we have this model that saves the files then by selecting each one as default it well be the only returned record.
        Default will be updated in Admin panel then others will be updated in a signal
    """
    title = models.CharField(max_length=255, verbose_name="File Title")
    file = models.FileField(upload_to='landing/%Y/%m/%d/', verbose_name="File")
    is_default = models.BooleanField(default=False, verbose_name="Is Default")
    @property
    def file_type(self):
        """
        Returns file type based on mime-type
        Example: image/jpeg or video/mp4
        """
        mime_type, encoding = mimetypes.guess_type(self.file.url)
        return mime_type or 'unknown'

    @property
    def is_image(self):
        mime = self.file_type
        return mime is not None and mime.startswith('image/')

    @property
    def is_video(self):
        mime = self.file_type
        return mime is not None and mime.startswith('video/')

    def __str__(self):
        return self.title


from django.db import models

class Subscriber(models.Model):
    phone = models.CharField(max_length=11, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone

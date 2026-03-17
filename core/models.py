from django.db import models
from django.utils import translation


class Banner(models.Model):
    """Hero banner carousel for homepage."""

    image = models.ImageField(upload_to="banners/")
    image_mobile = models.ImageField(
        upload_to="banners/mobile/",
        blank=True,
        help_text="Optional mobile-specific image",
    )
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.TextField(blank=True)
    title_ar = models.CharField(
        max_length=200, blank=True, verbose_name="Title (Arabic)"
    )
    subtitle_ar = models.TextField(blank=True, verbose_name="Subtitle (Arabic)")
    link = models.URLField(blank=True)
    link_text = models.CharField(max_length=50, blank=True)
    link_text_ar = models.CharField(
        max_length=50, blank=True, verbose_name="Link Text (Arabic)"
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __str__(self):
        return self.title or f"Banner #{self.id}"

    @property
    def get_title(self):
        lang = translation.get_language()
        if lang == "ar" and self.title_ar:
            return self.title_ar
        return self.title

    @property
    def get_subtitle(self):
        lang = translation.get_language()
        if lang == "ar" and self.subtitle_ar:
            return self.subtitle_ar
        return self.subtitle

    @property
    def get_link_text(self):
        lang = translation.get_language()
        if lang == "ar" and self.link_text_ar:
            return self.link_text_ar
        return self.link_text or "Shop Now"

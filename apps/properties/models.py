from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Property(models.Model):
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties")
    title = models.CharField(max_length=200)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(1)])
    max_guests = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price_per_night__gt=0), name="property_price_positive"),
            models.CheckConstraint(condition=models.Q(max_guests__gte=1), name="property_max_guests_min_1"),
        ]

    def __str__(self):
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Image for {self.property}"

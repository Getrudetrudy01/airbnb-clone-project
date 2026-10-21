from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Review(models.Model):
    # One review per stay: tying the review to a booking proves the author actually stayed there.
    booking = models.OneToOneField("bookings.Booking", on_delete=models.CASCADE, related_name="review")
    property = models.ForeignKey("properties.Property", on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="review_rating_1_to_5"),
        ]

    def __str__(self):
        return f"{self.rating}★ for {self.property} by {self.author}"

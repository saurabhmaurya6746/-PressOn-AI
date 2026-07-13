from django.db import models


class HandMeasurement(models.Model):

    image = models.ImageField(upload_to="uploads/")

    thumb = models.FloatField(default=0)

    index = models.FloatField(default=0)

    middle = models.FloatField(default=0)

    ring = models.FloatField(default=0)

    little = models.FloatField(default=0)

    recommended_size = models.CharField(
        max_length=30,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Measurement {self.id}"
    

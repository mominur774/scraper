from django.db import models

# Create your models here.

class User(models.Model):
    email = models.EmailField(max_length=255)
    password = models.CharField(max_length=255)
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = 'Slintel User'
        verbose_name_plural = 'Slintel Users'
from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name")
    price = models.DecimalField(max_digits=5, decimal_places=2)

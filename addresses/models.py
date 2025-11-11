from django.db import models
from django.utils import timezone

class Address(models.Model):
    address = models.CharField(max_length=70,
                               unique=True,
                               verbose_name='Адрес места')
    lat = models.DecimalField(max_digits=11,
                              decimal_places=8,
                              verbose_name='Широта')
    lon = models.DecimalField(max_digits=11,
                              decimal_places=8,
                              verbose_name='Долгота')
    request_date = models.DateField(
        default=timezone.now,
        verbose_name='Дата запроса к геокодеру'
    )

    def __str__(self):
        return self.address
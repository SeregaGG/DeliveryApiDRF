from django.db import models

# Create your models here.


class Contact(models.Model):
    name: str = models.CharField(max_length=255, default='name')
    surname: str = models.CharField(max_length=255, default='surname')
    phone: str = models.CharField(max_length=255, default='phone')
    address: str = models.CharField(max_length=255, default='address')


class Deal(models.Model):
    title: str = models.CharField(max_length=255, default='title')
    description: str = models.CharField(max_length=255, default='description')
    products: list = models.CharField(max_length=255, default='products')
    delivery_address: str = models.CharField(max_length=255, default='delivery_address')
    delivery_date: str = models.CharField(max_length=255, default='delivery_date')
    delivery_code: str = models.CharField(max_length=255, default='delivery_code')

    def __eq__(self, other):
        if isinstance(other, Deal):
            return (self.delivery_date == other.delivery_date
                    and sorted(self.products) == sorted(other.products)
                    and self.delivery_address == other.delivery_address)
        return NotImplemented


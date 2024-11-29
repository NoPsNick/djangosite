# Generated by Django 5.1.3 on 2024-11-22 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_remove_order_status_changed_item_product_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='name',
            field=models.CharField(blank=True, default='', max_length=50, null=True, verbose_name='Nome do produto'),
        ),
        migrations.AddField(
            model_name='item',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True, verbose_name='Preço'),
        ),
    ]

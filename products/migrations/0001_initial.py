# Generated by Django 5.1.3 on 2024-11-11 10:45

import autoslug.fields
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, monitor='status', verbose_name='status changed')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Nome')),
                ('description', models.TextField(blank=True, max_length=255, null=True, verbose_name='Descrição')),
                ('starts_at', models.DateTimeField(verbose_name='Data do começo')),
                ('expires_at', models.DateTimeField(verbose_name='Data do fim')),
                ('status', models.CharField(choices=[('Expirado', 'Expirado'), ('Ativo', 'Ativo'), ('Pendente', 'Pendente')], default='Pendente', max_length=10, verbose_name='Estado')),
                ('changed_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço em promoção')),
                ('original_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Preço original')),
            ],
            options={
                'verbose_name': 'promoção',
                'verbose_name_plural': 'promoções',
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='PromotionCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Nome')),
                ('description', models.TextField(blank=True, max_length=255, null=True, verbose_name='Descrição')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Código')),
                ('status', models.BooleanField(default=True, verbose_name='Está ativo?')),
                ('can_with_promotion', models.BooleanField(default=False, verbose_name='Pode ser usado com outra promoção?')),
                ('usable_in_roles', models.BooleanField(default=False, verbose_name='Pode ser usado em cargos?')),
                ('discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Valor do desconto')),
                ('discount_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Porcentagem de desconto')),
                ('usage_limit', models.PositiveIntegerField(default=1, verbose_name='Limite de uso global')),
                ('usage_count', models.PositiveIntegerField(default=0, verbose_name='Contagem de uso global')),
                ('user_usage_limit', models.PositiveIntegerField(default=1, verbose_name='Limite de uso por usuário')),
                ('start_at', models.DateTimeField(blank=True, null=True, verbose_name='Início da validade')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expira em')),
            ],
            options={
                'verbose_name': 'Código Promocional',
                'verbose_name_plural': 'Códigos Promocionais',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='PromotionCodeUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('user_usage_count', models.PositiveIntegerField(default=0, verbose_name='Contagem de uso por usuário')),
            ],
            options={
                'verbose_name': 'Uso do Código Promocional',
                'verbose_name_plural': 'Usos de Códigos Promocionais',
            },
        ),
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('units', models.PositiveIntegerField(default=0, help_text='Quantidade disponível no estoque.', verbose_name='Unidades em estoque')),
                ('units_sold', models.PositiveIntegerField(default=0, help_text='Quantidade de unidades vendidas.', verbose_name='Quantidade vendida')),
                ('units_hold', models.PositiveIntegerField(default=0, help_text='Quantidade de unidades vendidas que o pagamento não foi confirmado ainda.', verbose_name='Quantidade vendida em estágio de confirmação')),
            ],
            options={
                'verbose_name': 'estoque',
                'verbose_name_plural': 'estoques',
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Nome')),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name', unique=True)),
            ],
            options={
                'verbose_name': 'categoria',
                'verbose_name_plural': 'categorias',
                'ordering': ('name',),
                'indexes': [models.Index(fields=['slug'], name='products_ca_slug_da4386_idx')],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('is_role', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=255, verbose_name='Nome')),
                ('slug', autoslug.fields.AutoSlugField(always_update=True, editable=False, populate_from='name', unique=True)),
                ('image', models.ImageField(blank=True, upload_to='products/%Y/%m/%d', verbose_name='Imagem')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preço')),
                ('is_available', models.BooleanField(default=True, verbose_name='Está disponível?')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.category')),
            ],
            options={
                'verbose_name': 'produto',
                'verbose_name_plural': 'produtos',
                'ordering': ['-modified'],
            },
        ),
    ]

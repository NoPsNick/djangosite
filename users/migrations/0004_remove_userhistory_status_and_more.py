# Generated by Django 5.1.3 on 2024-11-19 15:29

import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_role_status_changed_remove_user_role'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userhistory',
            name='status',
        ),
        migrations.RemoveField(
            model_name='userhistory',
            name='status_changed',
        ),
        migrations.AddField(
            model_name='userhistory',
            name='created',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created'),
        ),
        migrations.AddField(
            model_name='userhistory',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified'),
        ),
        migrations.AddField(
            model_name='userhistory',
            name='type',
            field=models.CharField(choices=[('user_balance', 'Uso do saldo'), ('user_refund', 'Reembolso'), ('payment_create', 'Pagamento criado'), ('payment_success', 'Pagamento efetuado com sucesso'), ('payment_fail', 'Pagamento falhou')], default='user_balance', max_length=50, verbose_name='Tipo'),
        ),
        migrations.AlterField(
            model_name='role',
            name='status',
            field=models.CharField(choices=[('expirado', 'Expirado'), ('ativo', 'Ativo'), ('pendente', 'Pendente')], default='pendente', max_length=10, verbose_name='Status'),
        ),
    ]

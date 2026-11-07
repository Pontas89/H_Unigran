"""Troca o model antigo Account pelo Aluno (usuário de verdade do Django).

1. Cria o Aluno (proxy do User: mesma tabela que o login usa)
2. Converte cada Account antigo em um User que consegue fazer login
3. Apaga a tabela antiga de Account
"""
from django.contrib.auth.hashers import make_password
from django.db import migrations


def converter_accounts_em_usuarios(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    User = apps.get_model('auth', 'User')
    Perfil = apps.get_model('game', 'Perfil')

    for conta in Account.objects.all():
        if User.objects.filter(username=conta.username).exists():
            continue
        user = User.objects.create(
            username=conta.username,
            email=conta.email,
            password=make_password(conta.password),  # a senha antiga era texto puro: agora vira hash
        )
        Perfil.objects.get_or_create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '__latest__'),
        ('game', '0003_carga_inicial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Aluno',
            fields=[],
            options={
                'verbose_name': 'Aluno',
                'verbose_name_plural': 'Alunos',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('auth.user',),
        ),
        migrations.RunPython(converter_accounts_em_usuarios, migrations.RunPython.noop),
        migrations.DeleteModel(name='Account'),
    ]

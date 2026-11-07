from django.contrib.auth.models import User


class Aluno(User):
    """Aluno do Estudaí.

    É um "proxy" do User do Django: usa a MESMA tabela de usuários do login,
    só aparece separado no /admin com o nome "Alunos". Assim, todo aluno
    cadastrado aqui consegue entrar no sistema (a senha é salva com segurança).
    """

    class Meta:
        proxy = True
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'

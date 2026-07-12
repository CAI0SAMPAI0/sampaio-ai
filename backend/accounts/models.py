from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        if password:
            user.plain_password = password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField('Endereço de Email', unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    level = models.CharField(
        'Nível de Programação',
        max_length=20,
        default='iniciante',
        choices=[
            ('iniciante', 'Iniciante'),
            ('junior', 'Júnior'),
            ('pleno', 'Pleno'),
            ('senior', 'Sênior')
        ]
    )
    whatsapp_number = models.CharField('WhatsApp (WAHA)', max_length=50, blank=True, null=True)
    plain_password = models.CharField('Senha em Texto Plano', max_length=128, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class StoredFile(models.Model):
    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
    size = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


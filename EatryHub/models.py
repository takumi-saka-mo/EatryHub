from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class Store(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    username = models.CharField(
        'ユーザー名',
        max_length=150,
        unique=True,
        help_text='日本語・英数字・記号を使用できます',
        validators=[RegexValidator(
            regex=r'^[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\w.@+-]+$',
            message='ユーザー名には日本語（漢字・ひらがな・カタカナ）、英数字、@/./+/-/_ のみ使用可能です'
        )],
        error_messages={'unique': "このユーザー名は既に存在します。"},
    )
    additional_field = models.CharField(max_length=255, blank=True, null=True)
    # storeフィールド(店舗ごとの閲覧が可能)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',
        blank=True
    )

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
        
class TableUsage(models.Model):
    table_number = models.CharField(max_length=10)
    start_time   = models.DateTimeField()
    end_time     = models.DateTimeField()
    progress     = models.FloatField(default=0.0)


# home表示chartデータを再構成

class TableStructure(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)  # 店舗ごと
    table_number = models.IntegerField()
    capacity = models.IntegerField(default=4)  # 座席の定員(将来的に実装予定)

    class Meta:
        unique_together = ('store', 'table_number')  # 同じ店舗内でテーブル番号は一意

    def __str__(self):
        return f"{self.store.name} - {self.table_number}卓"
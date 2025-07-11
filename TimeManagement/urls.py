from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'TimeManagement'

urlpatterns = [
    path('', views.table_view, name='table_view'),
    path('update/', views.update_cell, name='update_cell'),
    path('update_cell/', views.update_cell, name='update_cell'),
    path('table-data-api/', views.table_data_api, name='table_data_api'), # モバイル用API
    path("mobile-view/", views.mobile_view, name="mobile_view"), # モバイルビュー専用
    path("duplicate_error/", TemplateView.as_view(template_name='help/duplicate_error.html'), name="duplicate_error"), # テーブル重複エラー復旧説明画面
    
    # {% url 'help:duplicate_error' %}
]

# DEBUG=True のときだけ静的ファイルを提供
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
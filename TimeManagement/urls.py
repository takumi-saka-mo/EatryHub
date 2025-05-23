from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

app_name = 'TimeManagement'

urlpatterns = [
    path('', views.table_view, name='table_view'),
    path('update/', views.update_cell, name='update_cell'),
    path('update_cell/', views.update_cell, name='update_cell'),
    path('table-data-api/', views.table_data_api, name='table_data_api'), # モバイル用API
    path("mobile-view/", views.mobile_view, name="mobile_view"), # モバイルビュー専用
]

# DEBUG=True のときだけ静的ファイルを提供
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

app_name = 'TimeManagement'

urlpatterns = [
    path('', views.table_view, name='table_view'),
    path('update/', views.update_cell, name='update_cell'),
    path('update_cell/', views.update_cell, name='update_cell'),
]

# DEBUG=True のときだけ静的ファイルを提供
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
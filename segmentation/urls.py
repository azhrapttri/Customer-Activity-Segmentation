from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'),
    path('predict/', views.predict, name='predict'),
    path('run-etl/', views.run_etl, name='run_etl'),
    path('run-kmeans/', views.run_kmeans, name='run_kmeans'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('api/kmeans-predict/', views.api_kmeans_predict, name='api_kmeans_predict'),
    path('api/chart-data/', views.api_chart_data, name='api_chart_data'),
]
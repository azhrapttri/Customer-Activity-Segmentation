import json
import joblib
import numpy as np
import csv
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.management import call_command
from django.conf import settings
from segmentation.models import CustomerActivityOLAP, ModelInfo


def dashboard(request):
    counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for obj in CustomerActivityOLAP.objects.values('kmeans_cluster'):
        level = obj['kmeans_cluster']
        if level in counts:
            counts[level] += 1

    model_info = ModelInfo.objects.filter(
        model_name='KMeans_CustomerActivity'
    ).order_by('-trained_at').first()

    context = {
        'counts_high':   counts['High'],
        'counts_medium': counts['Medium'],
        'counts_low':    counts['Low'],
        'total':         sum(counts.values()),
        'model_info':    model_info,
    }
    return render(request, 'segmentation/dashboard.html', context)


def customer_list(request):
    level_filter = request.GET.get('level', '')
    customers = CustomerActivityOLAP.objects.exclude(
        kmeans_cluster=None
    ).order_by('-total_rental')
    if level_filter:
        customers = customers.filter(kmeans_cluster=level_filter)
    context = {
        'customers':    customers,
        'level_filter': level_filter,
    }
    return render(request, 'segmentation/customer_list.html', context)


def predict(request):
    return render(request, 'segmentation/predict.html')


def run_etl(request):
    if request.method == 'POST':
        try:
            call_command('etl_customer_activity')
            messages.success(request, 'ETL completed successfully. Data has been updated.')
        except Exception as e:
            messages.error(request, f'ETL failed: {str(e)}')
    return redirect('dashboard')


def run_kmeans(request):
    if request.method == 'POST':
        try:
            call_command('train_kmeans')
            messages.success(request, 'K-Means clustering completed successfully.')
        except Exception as e:
            messages.error(request, f'K-Means failed: {str(e)}')
    return redirect('dashboard')


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customer_activity_segmentation.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Customer ID', 'First Name', 'Last Name',
        'Total Rental', 'Recency Days', 'Rental Frequency',
        'Avg Interval', 'K-Means Cluster', 'Last Updated'
    ])

    for c in CustomerActivityOLAP.objects.all().order_by('customer_id'):
        writer.writerow([
            c.customer_id, c.first_name, c.last_name,
            c.total_rental, c.recency_days, c.rental_frequency,
            c.avg_interval, c.kmeans_cluster,
            c.last_updated.strftime('%Y-%m-%d %H:%M')
        ])

    return response


@csrf_exempt
def api_kmeans_predict(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            total_rental     = float(data.get('total_rental', 0))
            rental_frequency = float(data.get('rental_frequency', 0))
            avg_interval     = float(data.get('avg_interval', 0))

            # Server-side validation
            if not (1 <= total_rental <= 500):
                return JsonResponse(
                    {'error': f'Total rental value {total_rental} is out of valid range (1–500).'},
                    status=422
                )
            if not (0.1 <= rental_frequency <= 100):
                return JsonResponse(
                    {'error': f'Rental frequency value {rental_frequency} is out of valid range (0.1–100).'},
                    status=422
                )
            if not (0.1 <= avg_interval <= 365):
                return JsonResponse(
                    {'error': f'Average interval value {avg_interval} is out of valid range (0.1–365).'},
                    status=422
                )

            model_dir   = os.path.join(settings.BASE_DIR, 'ml_models')
            kmeans      = joblib.load(os.path.join(model_dir, 'kmeans_model.pkl'))
            scaler      = joblib.load(os.path.join(model_dir, 'kmeans_scaler.pkl'))
            cluster_map = joblib.load(os.path.join(model_dir, 'kmeans_mapping.pkl'))

            features        = np.array([[total_rental, rental_frequency, avg_interval]])
            features_scaled = scaler.transform(features)
            cluster         = kmeans.predict(features_scaled)[0]
            prediction      = cluster_map[cluster]

            distances  = kmeans.transform(features_scaled)[0]
            total_dist = sum(1/d for d in distances)
            confidence = {
                cluster_map[i]: round((1/d) / total_dist * 100, 1)
                for i, d in enumerate(distances)
            }

            return JsonResponse({'prediction': prediction, 'confidence': confidence})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def api_chart_data(request):
    counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for obj in CustomerActivityOLAP.objects.values('kmeans_cluster'):
        level = obj['kmeans_cluster']
        if level in counts:
            counts[level] += 1
    return JsonResponse(counts)
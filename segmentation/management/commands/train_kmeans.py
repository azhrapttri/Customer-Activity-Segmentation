import os
import joblib
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.conf import settings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from segmentation.models import CustomerActivityOLAP, ModelInfo


class Command(BaseCommand):
    help = 'Train K-Means clustering model for customer activity segmentation'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting K-Means clustering...')

        # ── STEP 1: Load data ──────────────────────────────────────────────────
        qs = CustomerActivityOLAP.objects.all().values(
            'customer_id', 'total_rental', 'rental_frequency', 'avg_interval'
        )

        if not qs.exists():
            self.stdout.write(self.style.ERROR('OLAP table is empty. Run ETL first.'))
            return

        df = pd.DataFrame(list(qs))
        self.stdout.write(f'Data loaded: {len(df)} rows')

        # ── STEP 2: Define features ────────────────────────────────────────────
        FEATURES = ['total_rental', 'rental_frequency', 'avg_interval']
        X = df[FEATURES]

        # ── STEP 3: Scale data ────────────────────────────────────────────────
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        self.stdout.write('Data scaled')

        # ── STEP 4: Train K-Means ─────────────────────────────────────────────
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        self.stdout.write('K-Means trained')

        # ── STEP 5: Evaluate with Silhouette Score ────────────────────────────
        score = silhouette_score(X_scaled, kmeans.labels_)
        self.stdout.write(f'Silhouette Score: {score:.4f}')
        self.stdout.write('   (Range: -1 to 1, higher is better)')

        # ── STEP 6: Interpret clusters ─────────────────────────────────────────
        df['cluster'] = kmeans.labels_
        cluster_summary = df.groupby('cluster')[FEATURES].mean()

        self.stdout.write(f'\nCluster Summary:\n{cluster_summary.to_string()}')

        # Sort by avg_interval ascending (short interval = High, long interval = Low)
        sorted_by_interval = cluster_summary['avg_interval'].sort_values(ascending=True)

        cluster_map = {}
        labels = ['High', 'Medium', 'Low']
        for i, (cluster_id, _) in enumerate(sorted_by_interval.items()):
            cluster_map[cluster_id] = labels[i]

        self.stdout.write(f'\n🏷️ Cluster Mapping: {cluster_map}')

        # Verify mapping
        self.stdout.write('\nCluster Verification:')
        for cluster_id, label in cluster_map.items():
            row = cluster_summary.loc[cluster_id]
            self.stdout.write(
                f'   {label}: rental={row["total_rental"]:.1f}, '
                f'frequency={row["rental_frequency"]:.1f}, '
                f'interval={row["avg_interval"]:.1f}'
            )

        # ── STEP 7: Update OLAP table ──────────────────────────────────────────
        df['kmeans_label'] = df['cluster'].map(cluster_map)
        updated = 0
        for _, row in df.iterrows():
            CustomerActivityOLAP.objects.filter(
                customer_id=row['customer_id']
            ).update(kmeans_cluster=row['kmeans_label'])
            updated += 1

        self.stdout.write(f'\nUpdated {updated} customers with K-Means cluster')

        # Check distribution
        distribution = df['kmeans_label'].value_counts()
        self.stdout.write(f'\nK-Means Distribution:')
        for label, count in distribution.items():
            self.stdout.write(f'   {label}: {count} customers')

        # ── STEP 8: Save model + scaler + mapping ──────────────────────────────
        model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(model_dir, exist_ok=True)

        kmeans_path  = os.path.join(model_dir, 'kmeans_model.pkl')
        scaler_path  = os.path.join(model_dir, 'kmeans_scaler.pkl')
        mapping_path = os.path.join(model_dir, 'kmeans_mapping.pkl')

        joblib.dump(kmeans, kmeans_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(cluster_map, mapping_path)

        self.stdout.write(f'Model saved: {kmeans_path}')
        self.stdout.write(f'Scaler saved: {scaler_path}')
        self.stdout.write(f'Mapping saved: {mapping_path}')

        # ── STEP 9: Save model info to database ────────────────────────────────
        ModelInfo.objects.create(
            model_name      = 'KMeans_CustomerActivity',
            model_file      = kmeans_path,
            accuracy        = round(score, 4),
            total_customers = len(df),
            notes           = f'Silhouette Score: {score:.4f} | Features: {", ".join(FEATURES)} | Mapping: {cluster_map}'
        )

        self.stdout.write(self.style.SUCCESS('\nK-Means clustering completed!'))
from django.core.management.base import BaseCommand
from django.db import connections
from segmentation.models import CustomerActivityOLAP, CustomerDim, CustomerActivityFact


class Command(BaseCommand):
    help = 'ETL: Extract from DVD Rental, Transform, Load into OLAP tables'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting ETL...')

        # ── EXTRACT ───────────────────────────────────────────────────────────
        query = """
            WITH last_date AS (
                SELECT MAX(rental_date) AS max_date FROM rental
            )
            SELECT
                c.customer_id,
                c.first_name,
                c.last_name,
                COUNT(r.rental_id) AS total_rental,
                COALESCE(SUM(p.amount), 0) AS total_payment,
                EXTRACT(DAY FROM (ld.max_date - MAX(r.rental_date)))::INT AS recency_days,
                ROUND(
                    COUNT(r.rental_id)::NUMERIC /
                    NULLIF(
                        EXTRACT(MONTH FROM AGE(MAX(r.rental_date), MIN(r.rental_date))), 0
                    ), 2
                ) AS rental_frequency,
                COALESCE(
                    ROUND(
                        EXTRACT(DAY FROM (MAX(r.rental_date) - MIN(r.rental_date)))::NUMERIC /
                        NULLIF(COUNT(r.rental_id) - 1, 0), 2
                    ), 0
                ) AS avg_interval
            FROM customer c
            JOIN rental r ON c.customer_id = r.customer_id
            LEFT JOIN payment p ON r.rental_id = p.rental_id
            CROSS JOIN last_date ld
            GROUP BY c.customer_id, c.first_name, c.last_name, ld.max_date
        """

        with connections['default'].cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        self.stdout.write(f'Extract complete: {len(rows)} customers found')

        # ── TRANSFORM ─────────────────────────────────────────────────────────
        def assign_label(total_rental, rental_frequency, avg_interval):
            if total_rental >= 30 and float(rental_frequency or 0) >= 5 and float(avg_interval or 0) <= 4:
                return 'High'
            elif total_rental <= 22 or (float(rental_frequency or 0) < 3 and float(avg_interval or 0) > 7):
                return 'Low'
            else:
                return 'Medium'

        # ── LOAD ──────────────────────────────────────────────────────────────
        loaded = 0
        for row in rows:
            (customer_id, first_name, last_name,
             total_rental, total_payment,
             recency_days, rental_frequency, avg_interval) = row

            activity_level = assign_label(total_rental, rental_frequency, avg_interval)

            # Load into OLAP table
            CustomerActivityOLAP.objects.update_or_create(
                customer_id=customer_id,
                defaults={
                    'first_name':        first_name,
                    'last_name':         last_name,
                    'total_rental':      total_rental,
                    'total_payment':     float(total_payment),
                    'recency_days':      recency_days,
                    'rental_frequency':  float(rental_frequency or 0),
                    'avg_interval':      float(avg_interval or 0),
                    'activity_level':    activity_level,
                }
            )

            # Load into Dimension Table
            customer_dim, _ = CustomerDim.objects.update_or_create(
                customer_id=customer_id,
                defaults={
                    'first_name': first_name,
                    'last_name':  last_name,
                }
            )

            # Load into Fact Table
            CustomerActivityFact.objects.update_or_create(
                customer=customer_dim,
                defaults={
                    'total_rental':     total_rental,
                    'total_payment':    float(total_payment),
                    'recency_days':     recency_days,
                    'rental_frequency': float(rental_frequency or 0),
                    'avg_interval':     float(avg_interval or 0),
                }
            )

            loaded += 1

        self.stdout.write(f'Load complete: {loaded} customers saved')
        self.stdout.write(self.style.SUCCESS('ETL completed!'))
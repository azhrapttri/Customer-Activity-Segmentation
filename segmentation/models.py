from django.db import models


# ── OLAP Table ────────────────────────────────────────────────────────────────
class CustomerActivityOLAP(models.Model):
    customer_id      = models.IntegerField(unique=True)
    first_name       = models.CharField(max_length=50)
    last_name        = models.CharField(max_length=50)
    total_rental     = models.IntegerField(default=0)
    total_payment    = models.FloatField(default=0.0)
    recency_days     = models.IntegerField(default=0)
    rental_frequency = models.FloatField(default=0.0)
    avg_interval     = models.FloatField(default=0.0)
    activity_level   = models.CharField(
        max_length=10,
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        null=True, blank=True
    )
    kmeans_cluster   = models.CharField(
        max_length=10,
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        null=True, blank=True
    )
    last_updated     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_activity_olap'

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.kmeans_cluster}"


# ── Model Info ────────────────────────────────────────────────────────────────
class ModelInfo(models.Model):
    model_name      = models.CharField(max_length=100)
    model_file      = models.CharField(max_length=255)
    accuracy        = models.FloatField()
    trained_at      = models.DateTimeField(auto_now_add=True)
    total_customers = models.IntegerField(default=0)
    notes           = models.TextField(blank=True)

    class Meta:
        db_table = 'model_info'

    def __str__(self):
        return f"{self.model_name} — {self.accuracy:.2f} ({self.trained_at.date()})"


# ── Dimension Table ───────────────────────────────────────────────────────────
class CustomerDim(models.Model):
    customer_id = models.IntegerField(unique=True)
    first_name  = models.CharField(max_length=50)
    last_name   = models.CharField(max_length=50)
    email       = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'segmentation_customer_dim'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ── Fact Table ────────────────────────────────────────────────────────────────
class CustomerActivityFact(models.Model):
    customer         = models.ForeignKey(CustomerDim, on_delete=models.CASCADE)
    total_rental     = models.IntegerField(default=0)
    total_payment    = models.FloatField(default=0.0)
    recency_days     = models.IntegerField(default=0)
    rental_frequency = models.FloatField(default=0.0)
    avg_interval     = models.FloatField(default=0.0)
    kmeans_cluster   = models.CharField(
        max_length=10,
        choices=[('High', 'High'), ('Medium', 'Medium'), ('Low', 'Low')],
        null=True, blank=True
    )
    last_updated     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'segmentation_customer_activity_fact'

    def __str__(self):
        return f"{self.customer.first_name} — {self.kmeans_cluster}"
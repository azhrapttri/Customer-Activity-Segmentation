# Customer Activity Segmentation System

An end-to-end machine learning system that segments DVD Rental customers into activity levels (**High**, **Medium**, **Low**) using unsupervised K-Means clustering. The system analyzes customer rental behavior to identify engagement patterns and support business decision-making.

---

## Features

- **ETL Pipeline** : Extracts raw rental data from PostgreSQL, calculates behavioral metrics, and loads into OLAP tables
- **K-Means Clustering** : Discovers natural customer segments without predefined rules or labels
- **Interactive Dashboard** : Visualizes cluster distribution and model performance metrics
- **Customer List** : Displays all customers with behavioral metrics, filterable by segment
- **Prediction Engine** : Predicts activity level for new or existing customers in real-time
- **Star Schema OLAP** : Structured dimension and fact tables following data warehouse principles
- **Model Management** : Saves, loads, and retrains models with automatic versioning

---

## Method & Concept

### Why K-Means Instead of Classification?

Initial approach used **Random Forest classification** with manually-defined labels, but this created **label leakage** the model achieved 100% accuracy because it simply memorized predefined rules rather than discovering patterns.

**Solution:** Switched to **K-Means clustering**, an unsupervised approach that:
- Requires **no predefined labels**
- Discovers **natural customer groupings** from behavioral similarity
- Produces **statistically sound results** (Silhouette Score: 0.556)
- Avoids **label leakage entirely**

### Key Behavioral Metrics

The model uses **four** core metrics to understand customer engagement. **Two** are user inputs, **two** are automatically calculated:

| Metric | Type | Description | Range |
|--------|------|-------------|-------|
| **total_rental** | User Input | Total films rented by customer | 1–500 |
| **active_months** | User Input | Customer tenure in months | 1–60 |
| **rental_frequency** | Auto-Calculated | total_rental ÷ active_months | 0.1–100 |
| **avg_interval** | Auto-Calculated | Average days between consecutive rentals | 0.1–365 |

User provides `total_rental` and `active_months`; the system calculates `rental_frequency` and `avg_interval` automatically before passing to the K-Means model.

### Clustering Logic

Clusters are mapped to segments based on `avg_interval`:
- **High** : shortest average interval (most consistent rental behavior)
- **Medium** : moderate average interval
- **Low** : longest average interval (sporadic rental pattern)

---

## Tech Stack

**Backend:**
- Django 4.2
- PostgreSQL (DVD Rental Database)
- Python 3.10+

**Data Processing:**
- pandas : data manipulation
- NumPy : numerical computations
- scikit-learn : K-Means clustering, StandardScaler

**Frontend:**
- HTML5 + CSS3 (Vintage aesthetic with modern typography)
- Chart.js : interactive visualizations
- Vanilla JavaScript : form validation, API calls

**Database Design:**
- OLAP Tables (wide table for ML)
- Star Schema (dimension + fact tables)

---

## How to Run

### Prerequisites

- Python 3.10+
- PostgreSQL (DVD Rental database setup)
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/azhrapttri/customer-activity-segmentation.git
   cd customer-segmentation
```

2. **Create virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Configure database** in `config/settings.py`:
```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'dvdrental',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
```

5. **Run migrations**
```bash
   python manage.py migrate
```

6. **Start development server**
```bash
   python manage.py runserver
```
   The browser will automatically open to `http://127.0.0.1:8000/segmentation/`

### Running ETL & Model Training

From the Django admin or dashboard:

- **Refresh Data** : Runs ETL pipeline to update OLAP table
- **Run K-Means Clustering** : Trains and evaluates K-Means model
- **Export to CSV** : Downloads OLAP data for external analysis

Or via command line:
```bash
python manage.py etl_customer_activity
python manage.py train_kmeans
```

---

## Dashboard Screenshots

### Overview Dashboard
Shows cluster distribution, model metrics, and system actions.

<img width="1897" height="538" alt="image" src="https://github.com/user-attachments/assets/36832157-74c0-4e7b-bb6e-9a8915096d16" />
<img width="1892" height="876" alt="image" src="https://github.com/user-attachments/assets/7ff1529c-30e2-4c94-95e2-10a7cf40993c" />
<img width="1890" height="614" alt="image" src="https://github.com/user-attachments/assets/08298d4e-7a63-455c-b4f5-14fff5eb167d" />

### Customer List
Displays all 599 customers with behavioral metrics, filterable by segment.

<img width="1895" height="874" alt="image" src="https://github.com/user-attachments/assets/8f409941-d916-4aa9-a5e5-230853b57280" />

### Prediction Interface
Real-time prediction form with confidence scores for new customer data.

<img width="1892" height="871" alt="image" src="https://github.com/user-attachments/assets/bdf50ecf-2b2c-48e7-9371-1046bc42eee9" />

<img width="1890" height="874" alt="image" src="https://github.com/user-attachments/assets/44300b94-870f-4757-b494-583c4e41878a" />

---

## Results & Insights

### Clustering Results

| Segment | Count | Total Rental | Frequency/Month | Avg Interval (days) |
|---------|-------|--------------|-----------------|-------------------|
| **High** | 216 | 31.3 | 15.7 | 2.8 |
| **Medium** | 225 | 22.9 | 11.5 | 3.9 |
| **Low** | 158 | 27.6 | 3.5 | 10.1 |

### Key Insight

**Low activity customers rent sporadically, not infrequently.** Despite higher total rentals than Medium segment, Low customers have 2.6x longer rental intervals (10.1 vs 3.9 days), indicating inconsistent engagement. This pattern would be invisible to rule-based classification but clearly emerges from K-Means unsupervised learning.

### Model Performance

- **Silhouette Score:** 0.556 (good cluster separation)
- **Training Data:** 599 customers
- **Features Used:** 3 behavioral metrics
- **Clustering Method:** K-Means (k=3, StandardScaler preprocessing)

---

## Notes

### Dataset Context

The DVD Rental database is a legacy dataset from 2005 containing transactional records. All temporal metrics (recency, intervals) are calculated relative to the dataset's maximum rental date, not current date.

### Future Improvements

- Implement **hierarchical clustering** for more granular segmentation
- Add **time-series analysis** to track customer engagement over quarters
- Develop **churn prediction model** using actual historical churn data
- Create **recommendation engine** based on cluster preferences
- Build **automated re-engagement campaigns** triggered by Low → Medium transitions

### Author

Azzahra Puteri Kamilah

Advanced Database Course Project - Semester 5

---

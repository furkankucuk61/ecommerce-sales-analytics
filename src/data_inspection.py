
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

# CSV files
csv_files = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv"
}

# Load datasets
datasets = {}

for name, filename in csv_files.items():
    file_path = DATA_DIR / filename

    if not file_path.exists():
        print(f"File not found: {filename}")
        continue

    datasets[name] = pd.read_csv(file_path)

    print(f"{name}: {datasets[name].shape}")

print("\nAll available datasets loaded.")

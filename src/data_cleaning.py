
import pandas as pd
from pathlib import Path

# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. DATASET CONFIGURATION
# ==========================================

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

date_columns = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ],

    "order_items": [
        "shipping_limit_date"
    ],

    "reviews": [
        "review_creation_date",
        "review_answer_timestamp"
    ]
}


# ==========================================
# 3. DATA CLEANING PROCESS
# ==========================================

cleaned_datasets = {}

for name, filename in csv_files.items():

    file_path = RAW_DIR / filename

    print(f"\nProcessing: {filename}")

    df = pd.read_csv(file_path)

    original_rows = len(df)

    # --------------------------------------
    # Convert date columns
    # --------------------------------------

    if name in date_columns:

        for column in date_columns[name]:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    # --------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------

    if name == "geolocation":

        duplicate_count = df.duplicated().sum()

        df = df.drop_duplicates()

        print("Exact duplicates removed:", duplicate_count)

    # --------------------------------------
    # Handle missing product categories
    # --------------------------------------

    if name == "products":

        df["product_category_name"] = (
            df["product_category_name"]
            .fillna("Unknown")
        )

    # --------------------------------------
    # Geolocation validation
    # --------------------------------------

    if name == "geolocation":

        invalid_coordinates = (
            (df["geolocation_lat"] < -34) |
            (df["geolocation_lat"] > 6) |
            (df["geolocation_lng"] < -75) |
            (df["geolocation_lng"] > -32)
        )

        print(
            "Coordinates outside approximate Brazil bounds:",
            invalid_coordinates.sum()
        )

    # --------------------------------------
    # Save processed dataset
    # --------------------------------------

    output_path = PROCESSED_DIR / f"{name}_cleaned.csv"

    df.to_csv(output_path, index=False)

    cleaned_datasets[name] = df

    print("Original rows:", original_rows)
    print("Final rows:", len(df))
    print("Missing values:", df.isnull().sum().sum())
    print("Saved:", output_path.name)


print("\n===================================")
print("DATA CLEANING COMPLETED!")
print("===================================")

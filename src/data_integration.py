
import pandas as pd
from pathlib import Path

# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = DATA_DIR

# ==========================================
# 2. LOAD CLEANED DATASETS
# ==========================================

orders = pd.read_csv(DATA_DIR / "orders_cleaned.csv")
order_items = pd.read_csv(DATA_DIR / "order_items_cleaned.csv")
customers = pd.read_csv(DATA_DIR / "customers_cleaned.csv")
products = pd.read_csv(DATA_DIR / "products_cleaned.csv")
sellers = pd.read_csv(DATA_DIR / "sellers_cleaned.csv")
payments = pd.read_csv(DATA_DIR / "payments_cleaned.csv")
reviews = pd.read_csv(DATA_DIR / "reviews_cleaned.csv")
categories = pd.read_csv(
    DATA_DIR / "category_translation_cleaned.csv"
)

print("All datasets loaded successfully.")

# ==========================================
# 3. PREPARE DIMENSION TABLES
# ==========================================

# Customer dimension
dim_customers = customers.copy()

# Product dimension + English category names
dim_products = products.merge(
    categories,
    on="product_category_name",
    how="left",
    validate="many_to_one"
)

dim_products["product_category_name_english"] = (
    dim_products["product_category_name_english"]
    .fillna("unknown")
)

# Seller dimension
dim_sellers = sellers.copy()

# ==========================================
# 4. AGGREGATE PAYMENTS
# ==========================================

# One row per order
payment_summary = (
    payments
    .groupby("order_id", as_index=False)
    .agg(
        total_payment=("payment_value", "sum"),
        payment_count=("payment_value", "count"),
        payment_types=("payment_type", "nunique")
    )
)

# ==========================================
# 5. AGGREGATE REVIEWS
# ==========================================

# One row per order
review_summary = (
    reviews
    .groupby("order_id", as_index=False)
    .agg(
        average_review_score=("review_score", "mean"),
        review_count=("review_id", "nunique")
    )
)

# ==========================================
# 6. CREATE FACT ORDERS
# ==========================================

fact_orders = orders.merge(
    dim_customers,
    on="customer_id",
    how="left",
    validate="one_to_one",
    suffixes=("", "_customer")
)

fact_orders = fact_orders.merge(
    payment_summary,
    on="order_id",
    how="left",
    validate="one_to_one"
)

fact_orders = fact_orders.merge(
    review_summary,
    on="order_id",
    how="left",
    validate="one_to_one"
)

# ==========================================
# 7. CREATE FACT ORDER ITEMS
# ==========================================

fact_order_items = order_items.merge(
    dim_products,
    on="product_id",
    how="left",
    validate="many_to_one"
)

fact_order_items = fact_order_items.merge(
    dim_sellers,
    on="seller_id",
    how="left",
    validate="many_to_one"
)

# Calculate line-level sales amounts
fact_order_items["item_revenue"] = fact_order_items["price"]

fact_order_items["item_total_with_freight"] = (
    fact_order_items["price"]
    + fact_order_items["freight_value"]
)

# ==========================================
# 8. DATA VALIDATION
# ==========================================

print("\n========== DATA VALIDATION ==========")

print(
    "Original orders:",
    len(orders)
)

print(
    "Integrated orders:",
    len(fact_orders)
)

print(
    "Original order items:",
    len(order_items)
)

print(
    "Integrated order items:",
    len(fact_order_items)
)

print(
    "Unique order IDs:",
    fact_orders["order_id"].nunique()
)

print(
    "Unique customer IDs:",
    dim_customers["customer_id"].nunique()
)

# ==========================================
# 9. EXPORT TABLES
# ==========================================

output_tables = {
    "fact_orders": fact_orders,
    "fact_order_items": fact_order_items,
    "dim_customers": dim_customers,
    "dim_products": dim_products,
    "dim_sellers": dim_sellers
}

for name, df in output_tables.items():

    output_path = OUTPUT_DIR / f"{name}.csv"

    df.to_csv(output_path, index=False)

    print(f"Saved: {name}.csv | Rows: {len(df)}")

print("\nDATA INTEGRATION COMPLETED!")

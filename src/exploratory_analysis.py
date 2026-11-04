
import pandas as pd
from pathlib import Path

# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports" / "eda"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. LOAD DATA
# ==========================================
products = pd.read_csv(DATA_DIR / "dim_products.csv")

sellers = pd.read_csv(DATA_DIR / "dim_sellers.csv")

orders = pd.read_csv(DATA_DIR / "fact_orders.csv")

items = pd.read_csv(DATA_DIR / "fact_order_items.csv")

# Convert date columns
date_columns = [
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for column in date_columns:
    orders[column] = pd.to_datetime(
        orders[column],
        errors="coerce"
    )

print("Datasets loaded successfully!")


# ==========================================
# 3. DATA VALIDATION
# ==========================================

print("\n========== DATA VALIDATION ==========")

print("Missing order IDs:", orders["order_id"].isna().sum())
print("Duplicate order IDs:", orders["order_id"].duplicated().sum())

print("Missing product IDs:", items["product_id"].isna().sum())

print(
    "Unmatched order items:",
    (~items["order_id"].isin(orders["order_id"])).sum()
)

print(
    "Unmatched products:",
    (~items["product_id"].isin(products["product_id"])).sum()
)

print(
    "Unmatched sellers:",
    (~items["seller_id"].isin(sellers["seller_id"])).sum()
)


# ==========================================
# 4. ORDERS WITHOUT ITEMS
# ==========================================

print("\n========== ORDERS WITHOUT ITEMS ==========")

orders_with_items = items["order_id"].unique()

orders_without_items = orders[
    ~orders["order_id"].isin(orders_with_items)
]

print("Orders without matching items:", len(orders_without_items))

print("\nOrder statuses:")
print(orders_without_items["order_status"].value_counts())

print("\nDelivered orders without items:")
print(
    (orders_without_items["order_status"] == "delivered").sum()
)

print("\nSample records:")
print(
    orders_without_items[
        ["order_id", "order_status", "order_purchase_timestamp"]
    ].head(10)
)


# ==========================================
# 5. REVENUE CALCULATION
# ==========================================

items["price"] = pd.to_numeric(
    items["price"],
    errors="coerce"
)

items["freight_value"] = pd.to_numeric(
    items["freight_value"],
    errors="coerce"
)

# Calculate revenue at order-item level
items["item_revenue"] = items["price"]

items["item_total"] = (
    items["price"] + items["freight_value"]
)

# Aggregate item data by order
order_revenue = (
    items.groupby("order_id", as_index=False)
    .agg(
        total_revenue=("item_revenue", "sum"),
        total_freight=("freight_value", "sum"),
        total_with_freight=("item_total", "sum"),
        item_count=("order_item_id", "count")
    )
)

# Attach order information
sales = orders.merge(
    order_revenue,
    on="order_id",
    how="left",
    validate="one_to_one"
)

# Missing revenue is kept separate for investigation
print(
    "\nOrders without matching items:",
    sales["total_revenue"].isna().sum()
)

# Only completed orders for primary sales KPIs
delivered_sales = sales[
    sales["order_status"] == "delivered"
].copy()

delivered_sales["total_revenue"] = (
    delivered_sales["total_revenue"].fillna(0)
)


# ==========================================
# 6. MAIN BUSINESS KPIs
# ==========================================

total_orders = len(orders)

delivered_orders = delivered_sales["order_id"].nunique()

total_customers = (
    delivered_sales["customer_unique_id"].nunique()
)

total_revenue = delivered_sales["total_revenue"].sum()

average_order_value = (
    total_revenue / delivered_orders
    if delivered_orders > 0 else 0
)

average_review_score = (
    delivered_sales["average_review_score"].mean()
)

delivery_rate = (
    delivered_orders / total_orders * 100
    if total_orders > 0 else 0
)

kpi_results = pd.DataFrame({
    "KPI": [
        "Total Orders",
        "Delivered Orders",
        "Unique Customers",
        "Total Revenue",
        "Average Order Value",
        "Average Review Score",
        "Delivery Rate (%)"
    ],
    "Value": [
        total_orders,
        delivered_orders,
        total_customers,
        total_revenue,
        average_order_value,
        average_review_score,
        delivery_rate
    ]
})

print("\n========== BUSINESS KPIs ==========")

print(kpi_results.to_string(index=False))

kpi_results.to_csv(
    REPORT_DIR / "business_kpis.csv",
    index=False
)


# ==========================================
# 7. MONTHLY SALES ANALYSIS
# ==========================================

delivered_sales["order_month"] = (
    delivered_sales["order_purchase_timestamp"]
    .dt.to_period("M")
)

monthly_sales = (
    delivered_sales
    .groupby("order_month")
    .agg(
        total_revenue=("total_revenue", "sum"),
        total_orders=("order_id", "nunique"),
        total_customers=("customer_unique_id", "nunique")
    )
    .reset_index()
)

monthly_sales["order_month"] = (
    monthly_sales["order_month"].astype(str)
)

monthly_sales = monthly_sales.sort_values(
    "order_month"
)

print("\n========== MONTHLY SALES ==========")

print(monthly_sales.to_string(index=False))

monthly_sales.to_csv(
    REPORT_DIR / "monthly_sales.csv",
    index=False
)


# ==========================================
# 8. PRODUCT CATEGORY ANALYSIS
# ==========================================

delivered_items = items.merge(
    orders[["order_id", "order_status"]],
    on="order_id",
    how="inner",
    validate="many_to_one"
)

delivered_items = delivered_items[
    delivered_items["order_status"] == "delivered"
].copy()

category_analysis = (
    delivered_items
    .groupby("product_category_name_english")
    .agg(
        total_revenue=("price", "sum"),
        total_items=("product_id", "count"),
        average_price=("price", "mean")
    )
    .reset_index()
    .sort_values(
        "total_revenue",
        ascending=False
    )
)

print("\n========== TOP 10 PRODUCT CATEGORIES ==========")

print(category_analysis.head(10).to_string(index=False))

category_analysis.to_csv(
    REPORT_DIR / "category_analysis.csv",
    index=False
)


# ==========================================
# 9. DELIVERY PERFORMANCE
# ==========================================

delivered_sales["delivery_delay_days"] = (
    delivered_sales["order_delivered_customer_date"]
    - delivered_sales["order_estimated_delivery_date"]
).dt.total_seconds() / 86400

delivery_analysis = delivered_sales[
    "delivery_delay_days"
].dropna()

average_delivery_delay = delivery_analysis.mean()

late_delivery_rate = (
    (delivery_analysis > 0).mean() * 100
    if len(delivery_analysis) > 0 else 0
)

print("\n========== DELIVERY PERFORMANCE ==========")

print("Average delivery delay (days):", average_delivery_delay)

print("Late delivery rate (%):", late_delivery_rate)


# ==========================================
# 10. EXPORT RESULTS
# ==========================================

print("\n========== EXPORTING RESULTS ==========")

print("Reports directory:", REPORT_DIR)

print("\nEDA ANALYSIS COMPLETED SUCCESSFULLY!")

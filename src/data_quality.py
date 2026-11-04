
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

csv_files = list(DATA_DIR.glob("*.csv"))

for file in csv_files:

    df = pd.read_csv(file)

    print("\n" + "=" * 60)
    print(f"DATASET: {file.name}")
    print("=" * 60)

    # Dataset dimensions
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])

    # Missing values
    print("\nMissing Values:")
    print(df.isnull().sum()[df.isnull().sum() > 0])

    # Duplicate rows
    print("\nDuplicate Rows:", df.duplicated().sum())

    # Data types
    print("\nData Types:")
    print(df.dtypes)

    # Basic statistics
    print("\nNumerical Statistics:")
    print(df.describe().round(2))

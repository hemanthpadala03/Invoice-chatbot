import os
import pandas as pd

# ----------------------------------------
# PATHS
# ----------------------------------------
INPUT_FOLDER = r"C:\Drive_d\Python\F-AI\T8\Input Docs"
OUTPUT_FOLDER = r"C:\Drive_d\Python\F-AI\T8\data"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

all_invoices = []
all_items = []


# ----------------------------------------
# HELPERS
# ----------------------------------------

def find_line_items_sheet(sheet_names):
    for s in sheet_names:
        if s.replace(" ", "").lower() == "line_items":
            return s
    return None


def detect_header_row(df_preview):
    for i in range(min(10, len(df_preview))):
        row = df_preview.iloc[i].astype(str).str.lower()
        if any("description" in cell for cell in row):
            return i
    return 0


def clean_column_names(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", "")
        .str.replace("\r", "")
        .str.strip()
        .str.replace(" ", "")
        .str.replace(".", "")
        .str.lower()
    )

    rename_map = {
        "slno": "SlNo",
        "description": "Description",
        "unitprice": "UnitPrice",
        "discount": "Discount",
        "qty": "Qty",
        "quantity": "Qty",
        "netamount": "NetAmount",
        "taxrate": "TaxRate",
        "taxtype": "TaxType",
        "taxamount": "TaxAmount",
        "totalamount": "TotalAmount"
    }

    df.rename(columns=rename_map, inplace=True)
    return df


def remove_summary_rows(df):
    if "Description" not in df.columns:
        return df

    mask = df["Description"].astype(str).str.contains(
        "total|gross|taxable|summary",
        case=False,
        na=False
    )
    return df[~mask]


# ----------------------------------------
# AMAZON CLEANING (ONLY SYMBOL REMOVAL)
# ----------------------------------------

def clean_amazon_currency(df, filename):

    if "amazon" not in filename.lower():
        return df

    currency_cols = [
        "UnitPrice",
        "Discount",
        "NetAmount",
        "TaxAmount",
        "TotalAmount"
    ]

    for col in currency_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("â‚¹", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.strip()
            )

    return df


# ----------------------------------------
# READ FILES
# ----------------------------------------
for file in os.listdir(INPUT_FOLDER):

    if not file.endswith(".xlsx"):
        continue

    print("Processing:", file)

    file_path = os.path.join(INPUT_FOLDER, file)
    source = file.split()[0]

    sheets = pd.read_excel(
        file_path,
        sheet_name=None,
        dtype=object
    )

    sheet_names = list(sheets.keys())

    # -------- SHEET 1 ----------
    invoice_df = sheets[sheet_names[0]].copy()
    invoice_df["source"] = source
    invoice_df["file_name"] = file
    all_invoices.append(invoice_df)

    # -------- SHEET 2 ----------
    line_sheet = find_line_items_sheet(sheet_names)

    if line_sheet is not None:

        preview = pd.read_excel(
            file_path,
            sheet_name=line_sheet,
            header=None,
            dtype=object
        )

        header_row = detect_header_row(preview)

        items_df = pd.read_excel(
            file_path,
            sheet_name=line_sheet,
            header=header_row,
            dtype=object
        )

        items_df = clean_column_names(items_df)
        items_df = remove_summary_rows(items_df)

        # ONLY currency symbol cleaning
        items_df = clean_amazon_currency(items_df, file)

        items_df["source"] = source
        items_df["file_name"] = file

        all_items.append(items_df)


# ----------------------------------------
# MERGE
# ----------------------------------------
master_invoices = pd.concat(all_invoices, ignore_index=True)
master_items = pd.concat(all_items, ignore_index=True)


# ----------------------------------------
# SAVE
# ----------------------------------------
master_invoices.to_csv(
    os.path.join(OUTPUT_FOLDER, "master_invoices.csv"),
    index=False
)

master_items.to_csv(
    os.path.join(OUTPUT_FOLDER, "master_items.csv"),
    index=False
)

print("\nDONE")
print("Invoices:", master_invoices.shape)
print("Items:", master_items.shape)

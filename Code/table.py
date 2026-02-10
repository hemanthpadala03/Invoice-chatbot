import os
import pandas as pd

# =========================
# PATHS
# =========================
INPUT_FOLDER = r"C:\Drive_d\Python\F-AI\T8\Input Docs"
OUTPUT_FILE = r"C:\Drive_d\Python\F-AI\T8\combined_line_items.xlsx"


# =========================
# HELPER FUNCTIONS
# =========================

def find_line_items_sheet(xls):
    """
    Find Line_Items sheet ignoring case and spaces
    """
    for s in xls.sheet_names:
        if s.replace(" ", "").lower() == "line_items":
            return s
    return None


def detect_header_row(df_preview):
    """
    Detect header row by locating 'description' column
    """
    for i in range(min(10, len(df_preview))):
        row = df_preview.iloc[i].astype(str).str.lower()

        if any("description" in cell for cell in row):
            return i

    return 0


def clean_column_names(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\n", "")   # remove line breaks
        .str.replace("\r", "")
        .str.strip()             # remove leading/trailing spaces
        .str.replace(" ", "")    # remove internal spaces
        .str.replace(".", "")
        .str.lower()             # make uniform
    )

    # Standard column mapping
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
    """
    Remove non-line-item rows
    """
    if "Description" not in df.columns:
        return df

    mask = df["Description"].astype(str).str.contains(
        "total|gross|taxable|summary",
        case=False,
        na=False
    )

    return df[~mask]


# =========================
# MAIN PROCESS
# =========================

all_data = []

for file in os.listdir(INPUT_FOLDER):

    if not file.endswith((".xlsx", ".xls")):
        continue

    file_path = os.path.join(INPUT_FOLDER, file)

    try:
        xls = pd.ExcelFile(file_path)

        sheet = find_line_items_sheet(xls)

        if sheet is None:
            print(f"Skipped {file} -> Line_Items sheet not found")
            continue

        # Preview first few rows
        preview = pd.read_excel(file_path, sheet_name=sheet, header=None)

        header_row = detect_header_row(preview)

        df = pd.read_excel(
            file_path,
            sheet_name=sheet,
            header=header_row
        )

        df = clean_column_names(df)

        # Standardize Description column name
        for col in df.columns:
            if col.lower() == "description":
                df.rename(columns={col: "Description"}, inplace=True)

        df = remove_summary_rows(df)

        df["Source_File"] = file

        all_data.append(df)

        print(f"Processed: {file}")

    except Exception as e:
        print(f"Skipped {file} -> {e}")


# =========================
# MERGE AND SAVE
# =========================

if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_excel(OUTPUT_FILE, index=False)
    print("\nSaved to:", OUTPUT_FILE)
else:
    print("No valid data found.")

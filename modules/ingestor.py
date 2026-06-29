# modules/ingestor.py
import re
import pandas as pd
from typing import Tuple

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

def process_upload(file_obj) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """
    Ingests CSV, strips Windows BOM markers, verifies schema, 
    sanitizes whitespace/casing, and splits into valid/invalid records.
    """
    try:
        # utf-8-sig automatically removes invisible Windows Excel Byte-Order Marks
        df = pd.read_csv(file_obj, dtype=str, encoding="utf-8-sig")
    except Exception:
        try:
            # Fallback if the user saved it in legacy Windows ANSI format
            file_obj.seek(0)
            df = pd.read_csv(file_obj, dtype=str, encoding="cp1252")
        except Exception as e:
            return pd.DataFrame(), pd.DataFrame(), f"Failed to parse CSV: {str(e)}"

    # Scrub invisible characters from Column Headers
    df.columns = [re.sub(r"[^\w]", "", col).strip().title() for col in df.columns]

    required = {"Name", "Email"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        return pd.DataFrame(), pd.DataFrame(), f"Schema Error: Missing columns {missing}. Found: {list(df.columns)}"

    df = df.fillna("")
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    df["Name"] = df["Name"].str.title()

    is_valid_email = df["Email"].apply(lambda x: bool(EMAIL_REGEX.match(x)))
    is_valid_name = df["Name"].str.len() > 0

    valid_mask = is_valid_email & is_valid_name

    valid_df = df[valid_mask].copy().reset_index(drop=True)
    invalid_df = df[~valid_mask].copy().reset_index(drop=True)

    valid_df["_record_id"] = valid_df.index.astype(str)

    return valid_df, invalid_df, "Success"
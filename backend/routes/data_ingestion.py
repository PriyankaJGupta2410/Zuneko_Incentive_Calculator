import shutil
from pydantic import ValidationError
from fastapi import APIRouter, UploadFile, File, Form,HTTPException
import os
import pandas as pd
import uuid
from datetime import datetime,date
from dotenv import load_dotenv
from models import SalesRow,StructuredRuleRow,AdHocSchemeRow
from database import get_connection
from dateutil import parser as date_parser
from typing import List,Dict
import re

load_dotenv()
data_ingestion_router = APIRouter()

##########################DIRECTORY TO SAVE UPLOADED FILES ##########################
UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
############################ API ROUTES FOR DATA INGESTION #########################
@data_ingestion_router.post("/upload_sales_data")
async def upload_sales_data(file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    # ---------- Save uploaded file ----------
    saved_file_path = os.path.join(UPLOAD_DIRECTORY, f"{uuid.uuid4()}_{file.filename}")
    try:
        with open(saved_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # ---------- Read CSV ----------
    try:
        df = pd.read_csv(saved_file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # ---------- Normalize headers ----------
    df.columns = [c.strip().lower() for c in df.columns]

    # ---------- Required columns ----------
    required_columns = [
        "employee_id", "branch", "role",
        "vehicle_model", "vehicle_type",
        "quantity", "sale_date"
    ]
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column: {col}")

    # ---------- Pandas data checks ----------
    # 1. Remove exact duplicate rows
    df.drop_duplicates(inplace=True)

    # 2. Check quantity >= 1
    if (df["quantity"] <= 0).any():
        raise HTTPException(status_code=400, detail="Quantity must be >= 1 for all rows")

    # 3. Validate sale_date format
    try:
        df["sale_date"] = pd.to_datetime(df["sale_date"], errors='raise').dt.date
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format in sale_date: {str(e)}")

    # ---------- Validate rows with Pydantic ----------
    rows = df.to_dict(orient="records")
    validated_rows: List[SalesRow] = []
    invalid_rows: List[Dict] = []

    for i, row in enumerate(rows):
        try:
            validated_row = SalesRow(**row)
            validated_rows.append(validated_row)
        except ValidationError as e:
            invalid_rows.append({"row_number": i + 2, "errors": e.errors()})  # +2 for CSV header & 0-index

    if not validated_rows:
        raise HTTPException(status_code=400, detail=f"All rows are invalid: {invalid_rows}")

    # ---------- DB connection ----------
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        # ---------- Insert into uploaded_files ----------
        upload_file_id = str(uuid.uuid4())
        insert_file_sql = """
        INSERT INTO uploaded_files (
            id, file_name, file_type, uploaded_at, created_at,
            total_records, invalid_rows_count, invalid_rows
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_file_sql,
            (
                upload_file_id,
                file.filename,
                "sales_csv",
                datetime.now(),
                datetime.now(),
                len(validated_rows),
                len(invalid_rows),
                str(invalid_rows)  # store as JSON string
            )
        )

        # ---------- Insert validated sales rows ----------
        insert_sales_sql = """
        INSERT INTO sales_transactions (
            id, employee_id, branch, role, vehicle_model,
            vehicle_type, quantity, sale_date, upload_file_id, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for row in validated_rows:
            cursor.execute(
                insert_sales_sql,
                (
                    str(uuid.uuid4()),
                    row.employee_id,
                    row.branch,
                    row.role,
                    row.vehicle_model,
                    row.vehicle_type,
                    row.quantity,
                    row.sale_date,
                    upload_file_id,
                    datetime.now()
                )
            )

        conn.commit()

        return {
            "status": True,
            "message": "Sales data uploaded successfully",
            "file_id": upload_file_id,
            "total_records": len(validated_rows),
            "invalid_rows_count": len(invalid_rows),
            "invalid_rows": invalid_rows,
            "saved_file": saved_file_path
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        cursor.close()
        conn.close()

@data_ingestion_router.post("/upload_structured_rule")
async def upload_structured_rule(file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    # ---------- Save uploaded file ----------
    saved_file_path = os.path.join(UPLOAD_DIRECTORY, f"{uuid.uuid4()}_{file.filename}")
    try:
        with open(saved_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # ---------- Read CSV ----------
    try:
        df = pd.read_csv(saved_file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # ---------- Normalize headers ----------
    df.columns = [c.strip().lower() for c in df.columns]

    # ---------- Required columns ----------
    required_columns = [
        "rule_id", "role", "vehicle_type",
        "min_units", "max_units",
        "incentive_amount_inr", "bonus_per_unit_inr",
        "valid_from", "valid_to", "rule_type"
    ]
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column: {col}")

    # ---------- Pandas checks ----------
    # 1. Remove duplicate rows
    df.drop_duplicates(inplace=True)

    # 2. Validate numeric columns
    numeric_cols = ["min_units", "max_units", "incentive_amount_inr", "bonus_per_unit_inr"]
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise HTTPException(status_code=400, detail=f"Column {col} must be numeric")

    # 3. Validate date columns
    try:
        df["valid_from"] = pd.to_datetime(df["valid_from"], errors='raise').dt.date
        df["valid_to"] = pd.to_datetime(df["valid_to"], errors='raise').dt.date
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format in valid_from/valid_to: {str(e)}")

    # ---------- Validate rows with Pydantic ----------
    rows = df.to_dict(orient="records")
    validated_rows: List[StructuredRuleRow] = []
    invalid_rows: List[Dict] = []

    for i, row in enumerate(rows):
        try:
            validated_row = StructuredRuleRow(**row)
            validated_rows.append(validated_row)
        except ValidationError as e:
            invalid_rows.append({"row_number": i + 2, "errors": e.errors()})

    if not validated_rows:
        raise HTTPException(status_code=400, detail=f"All rows are invalid: {invalid_rows}")

    # ---------- DB connection ----------
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    try:
        # ---------- Insert into uploaded_files ----------
        upload_file_id = str(uuid.uuid4())
        insert_file_sql = """
        INSERT INTO uploaded_files (
            id, file_name, file_type, uploaded_at, created_at,
            total_records, invalid_rows_count, invalid_rows
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_file_sql,
            (
                upload_file_id,
                file.filename,
                "structured_rule_csv",
                datetime.now(),
                datetime.now(),
                len(validated_rows),
                len(invalid_rows),
                str(invalid_rows)
            )
        )

        # ---------- Insert validated structured rules ----------
        insert_rule_sql = """
        INSERT INTO structured_rules (
            id, rule_id, role, vehicle_type, min_units, max_units,
            incentive_amount_inr, bonus_per_unit_inr, valid_from, valid_to,
            rule_type, upload_file_id, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for row in validated_rows:
            cursor.execute(
                insert_rule_sql,
                (
                    str(uuid.uuid4()),
                    row.rule_id,
                    row.role,
                    row.vehicle_type,
                    row.min_units,
                    row.max_units,
                    row.incentive_amount_inr,
                    row.bonus_per_unit_inr,
                    row.valid_from,
                    row.valid_to,
                    row.rule_type,
                    upload_file_id,
                    datetime.now()
                )
            )

        conn.commit()

        return {
            "status": True,
            "message": "Structured rules uploaded successfully",
            "file_id": upload_file_id,
            "total_records": len(validated_rows),
            "invalid_rows_count": len(invalid_rows),
            "invalid_rows": invalid_rows,
            "saved_file": saved_file_path
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    finally:
        cursor.close()
        conn.close()


@data_ingestion_router.post("/upload_ad_hoc_rule")
async def upload_ad_hoc_rule(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only TXT files allowed")

    # ---------- Save uploaded file ----------
    saved_file_path = os.path.join(UPLOAD_DIRECTORY, f"{uuid.uuid4()}_{file.filename}")
    content = await file.read()
    with open(saved_file_path, "wb") as f:
        f.write(content)

    # ---------- Read TXT ----------
    with open(saved_file_path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.strip():
        raise HTTPException(status_code=400, detail="TXT file is empty")

    # ---------- Extract schemes ----------
    scheme_pattern = r"\*SCHEME\s(\d+):(.*?)(?=\*SCHEME|\Z)"
    matches = re.findall(scheme_pattern, text, re.DOTALL | re.IGNORECASE)

    if not matches:
        raise HTTPException(status_code=400, detail="No schemes found in the TXT")

    validated_rows: List[Dict] = []
    invalid_rows: List[Dict] = []

    role_mapping = {
        "ASMs": "ASM",
        "RMs": "RM",
        "employees": "ALL",
        "All roles": "ALL"
    }

    def normalize_role(role_text: str):
        role_text = role_text.strip()
        for key, value in role_mapping.items():
            if key.lower() in role_text.lower():
                return value
        return role_text

    # ---------- Refined condition parser ----------
    def clean_condition(line: str):
        """Make condition human-readable instead of underscore format"""
        line = line.strip()
        line = re.sub(r"[\*]+", "", line)  # remove extra stars
        line = line.replace("_", " ")
        line = re.sub(r"\s+", " ", line)
        return line

    for scheme_id, scheme_text in matches:
        try:
            scheme_text = scheme_text.strip()
            lines = [line.strip("- ").strip() for line in scheme_text.split("\n") if line.strip()]
            if not lines:
                continue

            # ---------- Scheme name ----------
            scheme_name = lines[0].title()

            # ---------- Roles ----------
            role_match = re.search(r"Applicable to:\s*(.*?)\s*(?:Valid:|$)", scheme_text, re.IGNORECASE)
            default_roles = normalize_role(role_match.group(1).strip()) if role_match else "ALL"

            # ---------- Validity ----------
            valid_from, valid_to = None, None
            date_match = re.search(r"Valid:\s*(.*)", scheme_text, re.IGNORECASE)
            if date_match:
                date_text = date_match.group(1).strip()
                try:
                    if "-" in date_text:
                        parts = date_text.split("-")
                        valid_from = date_parser.parse(parts[0].strip(), dayfirst=False).date()
                        valid_to = date_parser.parse(parts[1].strip(), dayfirst=False).date()
                    else:
                        valid_from = valid_to = date_parser.parse(date_text, dayfirst=False).date()
                except Exception:
                    valid_from = date(2025, 9, 1)
                    valid_to = date(2025, 9, 30)
            else:
                valid_from = date(2025, 9, 1)
                valid_to = date(2025, 9, 30)

            # ---------- Process each line ----------
            for line in lines[1:]:
                if not line:
                    continue

                # Notes detection
                notes_keywords = ["promotional", "inventory", "base eligibility", "end of month",
                                  "schemes are cumulative", "branch target", "requires minimum",
                                  "insurance", "registration", "rules may change"]
                notes = ""
                if any(k.lower() in line.lower() for k in notes_keywords):
                    notes = line
                    validated_rows.append({
                        "scheme_id": int(scheme_id),
                        "scheme_name": scheme_name,
                        "condition": "",
                        "role": "ALL",
                        "bonus_amount": None,
                        "validity_from": valid_from,
                        "validity_to": valid_to,
                        "notes": notes
                    })
                    continue

                if line.startswith("Applicable to") or line.startswith("Valid") or line.startswith("NOTES"):
                    continue

                # ---------- Bonus amount ----------
                bonus_amount = None
                match_numeric = re.search(r"₹([\d,]+)", line)
                match_variable = re.search(r"(\d+\.?\d*\s*x)|Variable", line, re.IGNORECASE)
                if match_numeric:
                    bonus_amount = int(match_numeric.group(1).replace(",", ""))
                elif match_variable:
                    bonus_amount = match_variable.group(0).strip()

                # ---------- Role ----------
                role_line_match = re.search(r"All\s+([A-Za-z, ]+)", line)
                role = normalize_role(role_line_match.group(1).strip()) if role_line_match else default_roles

                # ---------- Condition ----------
                condition_text = clean_condition(line)

                validated_rows.append({
                    "scheme_id": int(scheme_id),
                    "scheme_name": scheme_name,
                    "condition": condition_text,
                    "role": role,
                    "bonus_amount": bonus_amount,
                    "validity_from": valid_from,
                    "validity_to": valid_to,
                    "notes": notes
                })

        except Exception as e:
            invalid_rows.append({"scheme_id": scheme_id, "error": str(e)})

    if not validated_rows:
        raise HTTPException(status_code=400, detail=f"All schemes invalid: {invalid_rows}")

    # ---------- Insert into DB ----------
    try:
        conn = get_connection()
        cursor = conn.cursor()

        upload_file_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO uploaded_files (
                id, file_name, file_type, uploaded_at, created_at,
                total_records, invalid_rows_count, invalid_rows
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            upload_file_id,
            file.filename,
            "ad_hoc_txt",
            datetime.now(),
            datetime.now(),
            len(validated_rows),
            len(invalid_rows),
            str(invalid_rows)
        ))

        insert_sql = """
        INSERT INTO ad_hoc_rules (
            scheme_id, scheme_name, conditions, role, bonus_amount,
            validity_from, validity_to, notes, upload_file_id, created_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        for row in validated_rows:
            cursor.execute(insert_sql, (
                row["scheme_id"],
                row["scheme_name"],
                row["condition"],
                row["role"],
                row["bonus_amount"],
                row["validity_from"],
                row["validity_to"],
                row["notes"],
                upload_file_id,
                datetime.now()
            ))
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return {
        "status": True,
        "message": "Ad-Hoc schemes uploaded successfully",
        "file_id": upload_file_id,
        "total_records": len(validated_rows),
        "invalid_rows_count": len(invalid_rows),
        "invalid_rows": invalid_rows,
        "saved_file": saved_file_path
    }

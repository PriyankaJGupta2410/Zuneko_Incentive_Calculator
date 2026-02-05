import shutil
from pydantic import ValidationError
from fastapi import APIRouter, UploadFile, File, Form,HTTPException
import os
import pandas as pd
from dotenv import load_dotenv
from models import SalesRowSchema,RuleRowSchema
from database import get_connection

load_dotenv()
data_ingestion_router = APIRouter()

##########################DIRECTORY TO SAVE UPLOADED FILES ##########################
UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
############################ API ROUTES FOR DATA INGESTION #########################
@data_ingestion_router.post("/upload_sales_data")
async def upload_sales_data(file: UploadFile = File(...)):
    try:
        # ------------------------------------
        # 1. File validation
        # ------------------------------------
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are allowed"
            )

        conn = get_connection()
        db = conn.cursor()

        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # ------------------------------------
        # 2. Load CSV
        # ------------------------------------
        try:
            df = pd.read_csv(file_path)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid CSV file format"
            )

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="Uploaded CSV file is empty"
            )

        # ------------------------------------
        # 3. Column validation
        # ------------------------------------
        REQUIRED_SALES_COLUMNS = [
            "Employee_ID",
            "Branch",
            "Role",
            "Vehicle_Model",
            "Quantity",
            "Sale_Date",
            "Vehicle_Type"
        ]

        missing_cols = [c for c in REQUIRED_SALES_COLUMNS if c not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"CSV structure is invalid. Missing columns: {missing_cols}"
            )

        # ------------------------------------
        # 4. Row processing
        # ------------------------------------
        success_count = 0
        failed_rows = []
        skipped_rows = 0

        for index, row in df.iterrows():
            try:
                row_dict = row.to_dict()

                # Skip empty rows
                if all(pd.isna(v) for v in row_dict.values()):
                    skipped_rows += 1
                    continue

                sales_data = SalesRowSchema(**row_dict)

                # Ensure salesperson exists
                db.execute(
                    "SELECT id FROM salespeople WHERE id=%s",
                    (sales_data.Employee_ID,)
                )
                if not db.fetchone():
                    db.execute(
                        """
                        INSERT INTO salespeople (id, branch, role)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            sales_data.Employee_ID,
                            sales_data.Branch,
                            sales_data.Role
                        )
                    )

                # Insert sales record
                db.execute(
                    """
                    INSERT INTO sales_records
                    (employee_id, vehicle_model, quantity, sale_date, vehicle_type)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        sales_data.Employee_ID,
                        sales_data.Vehicle_Model,
                        sales_data.Quantity,
                        sales_data.Sale_Date,
                        sales_data.Vehicle_Type
                    )
                )

                success_count += 1

            except ValidationError as ve:
                failed_rows.append({
                    "row_number": index + 2,
                    "type": "ValidationError",
                    "details": ve.errors()
                })

            except Exception as row_err:
                failed_rows.append({
                    "row_number": index + 2,
                    "type": "DatabaseError",
                    "details": str(row_err)
                })

        conn.commit()

        # ------------------------------------
        # 5. Message logic
        # ------------------------------------
        if success_count == 0:
            message = "Sales data upload failed for all rows"
        elif failed_rows:
            message = "Sales data uploaded with some failed rows"
        else:
            message = "Sales data uploaded successfully"

        return {
            "status": "success",
            "message": message,
            "file": file.filename,
            "summary": {
                "total_rows": len(df),
                "processed": success_count,
                "failed": len(failed_rows),
                "skipped": skipped_rows
            },
            "failed_rows": failed_rows
        }

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to process sales data"
        )

@data_ingestion_router.post("/upload_structured_rule")
async def upload_structured_rule(file: UploadFile = File(...)):

    conn = None
    try:
        # ------------------------------------
        # 1. File validation
        # ------------------------------------
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are allowed"
            )

        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # ------------------------------------
        # 2. Read CSV
        # ------------------------------------
        try:
            df = pd.read_csv(file_path)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid CSV file format"
            )

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="Uploaded CSV file is empty"
            )

        # ------------------------------------
        # 3. Validate required columns
        # ------------------------------------
        REQUIRED_RULE_COLUMNS = [
            "Rule_ID",
            "Role",
            "Vehicle_Type",
            "Min_Units",
            "Max_Units",
            "Incentive_Amount_INR",
            "Bonus_Per_Unit_INR",
            "Valid_From",
            "Valid_To"
        ]

        missing_cols = [c for c in REQUIRED_RULE_COLUMNS if c not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"CSV structure is invalid. Missing columns: {missing_cols}"
            )

        conn = get_connection()
        db = conn.cursor()

        # ------------------------------------
        # 4. Process rows
        # ------------------------------------
        success_count = 0
        failed_rows = []
        skipped_rows = 0

        for index, row in df.iterrows():
            try:
                row_dict = row.to_dict()

                # Skip completely empty rows
                if all(pd.isna(v) for v in row_dict.values()):
                    skipped_rows += 1
                    continue

                # Pydantic validation
                rule_data = RuleRowSchema(**row_dict)

                # Check duplicate rule
                db.execute(
                    "SELECT id FROM incentive_rules WHERE id = %s",
                    (rule_data.Rule_ID,)
                )
                if db.fetchone():
                    skipped_rows += 1
                    continue

                # Insert rule
                db.execute(
                    """
                    INSERT INTO incentive_rules
                    (
                        id,
                        role,
                        vehicle_type,
                        min_units,
                        max_units,
                        incentive_amount,
                        bonus_per_unit,
                        valid_from,
                        valid_to,
                        rule_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        rule_data.Rule_ID,
                        rule_data.Role,
                        rule_data.Vehicle_Type,
                        rule_data.Min_Units,
                        rule_data.Max_Units,
                        rule_data.Incentive_Amount_INR,
                        rule_data.Bonus_Per_Unit_INR,
                        rule_data.Valid_From,
                        rule_data.Valid_To,
                        "Structured"
                    )
                )

                success_count += 1

            except ValidationError as ve:
                failed_rows.append({
                    "row_number": index + 2,
                    "type": "ValidationError",
                    "details": ve.errors()
                })

            except Exception as row_err:
                failed_rows.append({
                    "row_number": index + 2,
                    "type": "DatabaseError",
                    "details": str(row_err)
                })

        conn.commit()

        # ------------------------------------
        # 5. Message logic
        # ------------------------------------
        if success_count == 0 and skipped_rows > 0:
            message = "All rules already exist. No new rules inserted"
        elif success_count == 0:
            message = "Rule upload failed for all rows"
        elif failed_rows:
            message = "Rules uploaded with some failed rows"
        else:
            message = "Rules uploaded successfully"

        return {
            "status": "success",
            "message": message,
            "file": file.filename,
            "summary": {
                "total_rows": len(df),
                "processed": success_count,
                "failed": len(failed_rows),
                "skipped": skipped_rows
            },
            "failed_rows": failed_rows
        }

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to process structured rule data"
        )

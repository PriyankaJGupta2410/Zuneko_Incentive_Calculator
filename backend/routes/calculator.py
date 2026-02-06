from fastapi import APIRouter, UploadFile, File, Form,HTTPException
import os
import pandas as pd
from dotenv import load_dotenv
from database import db,conn,get_connection
from datetime import date, datetime
from models import IncentiveCalculationRequest, EmployeeIncentive, IncentiveResponse
import json
import re
import calendar
import uuid


load_dotenv()
calculator_router = APIRouter()

############################ API ROUTES FOR CALCULATOR #########################
@calculator_router.post("/api/incentives/calculate")
def calculate_incentives(request: IncentiveCalculationRequest):
    try:
        # ---------- DB connection ----------
        conn = get_connection()
        cursor = conn.cursor()

        if not request.period:
            raise HTTPException(status_code=400, detail="Period is required")
        
        try:
            dt = datetime.strptime(request.period, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid period format. Expected YYYY-MM"
            )
        
        # ---------- Compute start and end dates ----------
        start_date = dt.date().replace(day=1)
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = start_date.replace(day=last_day)

        # ---------- Fetch all sales ----------
        sales_sql = f"""
        SELECT employee_id, role, vehicle_type, vehicle_model, SUM(quantity) AS total_quantity
        FROM sales_transactions
        WHERE sale_date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY employee_id, vehicle_type, role, vehicle_model
        """
        cursor.execute(sales_sql)
        sales_data = cursor.fetchall()
        if not sales_data:
            raise HTTPException(status_code=404, detail="No sales found for the period")

        df_sales = pd.DataFrame(sales_data)
        # ---------- Fetch structured rules ----------
        rules_sql = """
        SELECT * FROM structured_rules
        WHERE valid_from <= %s AND valid_to >= %s
        """
        cursor.execute(rules_sql, (end_date, start_date))
        structured_rules = cursor.fetchall()
        df_rules = pd.DataFrame(structured_rules)
        if not df_rules.empty:
            df_rules.columns = [c.lower() for c in df_rules.columns]
            df_rules['min_units'] = df_rules['min_units'].astype(int)
            df_rules['max_units'] = df_rules['max_units'].astype(int)
            df_rules['incentive_amount_inr'] = df_rules['incentive_amount_inr'].astype(float)
            df_rules['bonus_per_unit_inr'] = df_rules['bonus_per_unit_inr'].astype(float)
            df_rules['role'] = df_rules['role'].str.lower()
            df_rules['vehicle_type'] = df_rules['vehicle_type'].str.lower()

        # ---------- Fetch ad-hoc rules ----------
        adhoc_sql = """
        SELECT * FROM ad_hoc_rules
        WHERE validity_from <= %s AND validity_to >= %s
        """
        cursor.execute(adhoc_sql, (end_date, start_date))
        adhoc_rules = cursor.fetchall()
        df_ad_hoc = pd.DataFrame(adhoc_rules)
        if not df_ad_hoc.empty:
            df_ad_hoc.columns = [c.lower() for c in df_ad_hoc.columns]

        results = []

        # ---------- Iterate by employee ----------
        for emp_id, emp_sales in df_sales.groupby("employee_id"):
            structured_total = 0.0
            details_structured = []

            # ---------- Structured incentives ----------
            if not df_rules.empty:
                for _, sale in emp_sales.iterrows():
                    vehicle = str(sale['vehicle_type']).capitalize()
                    qty = int(sale['total_quantity'])
                    sale_role = str(sale['role']).lower()

                    matching_rules = df_rules[
                        (df_rules['role'] == sale_role) &
                        (df_rules['vehicle_type'] == sale['vehicle_type'].lower()) &
                        (qty >= df_rules['min_units']) &
                        (qty <= df_rules['max_units'])
                    ]

                    if matching_rules.empty:
                        continue

                    # pick the first matching rule (lowest min_units)
                    rule = matching_rules.sort_values('min_units').iloc[0]

                    bonus_units = max(0, qty - rule['min_units'])
                    structured_amount = rule['incentive_amount_inr'] + bonus_units * rule['bonus_per_unit_inr']
                    structured_total += structured_amount
                    details_structured.append({
                        "vehicle_model": sale['vehicle_model'],
                        "vehicle_type": sale['vehicle_type'],
                        "quantity": qty,
                        "rule_applied": rule['rule_id'],
                        "amount": structured_amount
                    })

            # ---------- Ad-Hoc incentives ----------
            ad_hoc_total = 0.0
            details_ad_hoc = []

            if not df_ad_hoc.empty:
                for _, scheme in df_ad_hoc.iterrows():
                    eligible_roles = [r.strip().lower() for r in str(scheme['role']).split(',')]
                    emp_role = str(emp_sales.iloc[0]['role']).lower()
                    if emp_role not in eligible_roles and 'all' not in eligible_roles:
                        continue  # Skip if employee not eligible

                    if scheme['bonus_amount']:
                        bonus_matches = re.findall(r"\d+", str(scheme['bonus_amount']).replace(",", ""))
                        for b in bonus_matches:
                            amount = float(b)
                            ad_hoc_total += amount
                            details_ad_hoc.append({
                                "scheme_name": scheme['scheme_name'],
                                "condition": scheme['conditions'],
                                "amount": amount
                            })

            total_incentive = structured_total + ad_hoc_total

            # ---------- Store calculation ----------
            calc_id = str(uuid.uuid4())
            insert_calc_sql = """
            INSERT INTO incentive_calculations (
                id, employee_id, total_incentive, structured_incentive, ad_hoc_incentive,
                calculation_date, details, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            details_json = json.dumps({"structured": details_structured, "ad_hoc": details_ad_hoc})
            cursor.execute(
                insert_calc_sql,
                (
                    calc_id,
                    emp_id,
                    total_incentive,
                    structured_total,
                    ad_hoc_total,
                    datetime.now(),
                    details_json,
                    datetime.now()
                )
            )

            results.append({
                "employee_id": emp_id,
                "total_incentive": total_incentive,
                "structured_incentive": structured_total,
                "ad_hoc_incentive": ad_hoc_total
            })

        conn.commit()
        return {"status": True, "message": "Incentives calculated", "data": results}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

    finally:
        cursor.close()
        conn.close()
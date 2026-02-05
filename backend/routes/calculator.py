from fastapi import APIRouter, UploadFile, File, Form,HTTPException
import os
import pandas as pd
from dotenv import load_dotenv
from database import db,conn,get_connection
from datetime import date, datetime
from models import IncentiveCalculationRequest
import json
import calendar


load_dotenv()
calculator_router = APIRouter()

############################ API ROUTES FOR CALCULATOR #########################
@calculator_router.post("/calculate-incentives")
def calculate_incentives_api(payload: IncentiveCalculationRequest):
    conn = None
    try:
        # ------------------------------------
        # 0. DB Connection
        # ------------------------------------
        conn = get_connection()
        db = conn.cursor()

        # ------------------------------------
        # 1. Validate & Parse period
        # ------------------------------------
        if not payload.period:
            raise HTTPException(status_code=400, detail="Period is required")

        try:
            dt = datetime.strptime(payload.period, "%Y-%m")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid period format. Expected YYYY-MM"
            )

        start_date = dt.date().replace(day=1)
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        end_date = start_date.replace(day=last_day)

        # ------------------------------------
        # 2. Fetch sales data
        # ------------------------------------
        db.execute(
            """
            SELECT employee_id, vehicle_type, quantity, sale_date
            FROM sales_records
            WHERE sale_date BETWEEN %s AND %s
            """,
            (start_date, end_date)
        )
        sales = db.fetchall()

        if not sales:
            return {
                "status": "success",
                "message": "No sales found for selected period",
                "processed_salespeople": 0
            }

        # ------------------------------------
        # 3. Group sales by employee
        # ------------------------------------
        sales_by_employee = {}
        for s in sales:
            sales_by_employee.setdefault(s["employee_id"], []).append(s)

        # ------------------------------------
        # 4. Load salespeople
        # ------------------------------------
        db.execute("SELECT id, branch, role FROM salespeople")
        emp_rows = db.fetchall()

        if not emp_rows:
            raise HTTPException(
                status_code=400,
                detail="Salespeople master data missing"
            )

        emp_map = {e["id"]: e for e in emp_rows}

        # ------------------------------------
        # 5. Branch totals
        # ------------------------------------
        branch_totals = {}
        for emp_id, emp_sales in sales_by_employee.items():
            emp = emp_map.get(emp_id)
            if not emp:
                continue
            branch = emp["branch"]
            branch_totals[branch] = branch_totals.get(branch, 0) + \
                                    sum(s["quantity"] for s in emp_sales)

        # ------------------------------------
        # 6. Load incentive rules
        # ------------------------------------
        db.execute(
            """
            SELECT *
            FROM incentive_rules
            WHERE rule_type='Structured'
              AND valid_from <= %s
              AND valid_to >= %s
            """,
            (end_date, start_date)
        )
        rules = db.fetchall()

        if not rules:
            raise HTTPException(
                status_code=400,
                detail="No active incentive rules found for this period"
            )

        processed = 0

        # ------------------------------------
        # 7. Per employee calculation
        # ------------------------------------
        for emp_id, emp_sales in sales_by_employee.items():
            emp = emp_map.get(emp_id)
            if not emp:
                continue

            role = emp["role"]
            branch = emp["branch"]

            sales_counts = {}
            boost_mid = boost_suv = 0

            for s in emp_sales:
                v_type = s["vehicle_type"]
                qty = s["quantity"]
                s_date = s["sale_date"]

                sales_counts[v_type] = sales_counts.get(v_type, 0) + qty

                if v_type == "Mid-Size Sedan" and date(2025,9,10) <= s_date <= date(2025,9,20):
                    boost_mid += qty
                if v_type == "SUV" and date(2025,9,15) <= s_date <= date(2025,9,25):
                    boost_suv += qty

            total_incentive = 0
            applied_rules = []

            # ---------- Structured slabs ----------
            for vehicle_type, count in sales_counts.items():
                candidates = [
                    r for r in rules
                    if r["role"] == role
                    and r["vehicle_type"] == vehicle_type
                    and r["min_units"] <= count
                    and (r["max_units"] is None or r["max_units"] >= count)
                ]

                if not candidates:
                    continue

                rule = max(candidates, key=lambda x: x["min_units"])

                base = rule["incentive_amount"]
                extra_units = count - rule["min_units"]
                calc_amt = base + (extra_units * rule["bonus_per_unit"])

                total_incentive += calc_amt

                applied_rules.append({
                    "rule_id": rule["id"],
                    "description": f"Structured {vehicle_type}",
                    "amount": round(calc_amt, 2)
                })

            # ---------- Ad-hoc ----------
            branch_total = branch_totals.get(branch, 0)
            achievement = (branch_total / 200) * 100

            if achievement >= 110:
                total_incentive += 10000
            elif achievement >= 95 and role == "RM":
                total_incentive += 8000
            elif achievement >= 80 and role == "ASM":
                total_incentive += 5000

            # ---------- Save ----------
            db.execute(
                "DELETE FROM calculation_results WHERE employee_id=%s AND period_month=%s",
                (emp_id, payload.period)
            )

            db.execute(
                """
                INSERT INTO calculation_results
                (employee_id, period_month, total_incentive,
                 breakdown_json, status, calculated_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (
                    emp_id,
                    payload.period,
                    round(total_incentive, 2),
                    json.dumps(applied_rules),
                    "Success",
                    date.today()
                )
            )

            processed += 1

        conn.commit()

        return {
            "status": "success",
            "message": "Incentives calculated successfully",
            "period": payload.period,
            "processed_salespeople": processed
        }

    # ---------------- EXCEPTIONS ----------------
    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        return {
            "status": "error",
            "message": "Internal calculation error",
            "error": str(e)
        }

    finally:
        if conn:
            conn.close()

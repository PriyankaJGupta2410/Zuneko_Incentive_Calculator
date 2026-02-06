from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import db, conn,get_connection
import json
from models import EmployeeIncentive,Summary,IncentiveResponse,TopPerformer,DashboardResponse,DashboardAPIResponse,IncentiveDetails
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

results_router = APIRouter()

############################ API ROUTES FOR RESULTS #########################

@results_router.get("/GETincentiveresults", response_model=IncentiveResponse)
async def GETincentiveresults():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch all incentive calculation records
        cursor.execute("SELECT * FROM incentive_calculations ORDER BY calculation_date DESC")
        incentive_rows = cursor.fetchall()

        if not incentive_rows:
            return {
                "status": True,
                "message": "No incentive results found",
                "summary": {"total_records": 0, "total_incentives": 0, "top_performer": None},
                "data": []
            }

        results = []
        top_performer = None

        for row in incentive_rows:
            details = json.loads(row.get("details", "{}"))

            # Total units from structured incentives
            total_units = sum(item.get("quantity", 0) for item in details.get("structured", []))

            # Fetch branch & role from sales_transactions table
            cursor.execute(
                "SELECT branch, role FROM sales_transactions WHERE employee_id = %s LIMIT 1",
                (row["employee_id"],)
            )
            sales_data = cursor.fetchone()
            branch = sales_data["branch"] if sales_data else "Unknown Branch"
            role = sales_data["role"] if sales_data else "Unknown Role"

            emp_incentive = EmployeeIncentive(
                employee_id=row["employee_id"],
                branch=branch,
                role=role,
                total_units=total_units,
                structured_incentive=float(row["structured_incentive"]),
                adhoc_incentive=float(row["ad_hoc_incentive"]),
                total_incentive=float(row["total_incentive"]),
                status="Completed" if float(row["total_incentive"]) > 0 else "Exception",
                details=IncentiveDetails(**details)
            )
            results.append(emp_incentive)

            # Determine top performer
            if not top_performer or emp_incentive.total_incentive > top_performer["total_incentive"]:
                top_performer = {
                    "employee_id": emp_incentive.employee_id,
                    "branch": emp_incentive.branch,
                    "role": emp_incentive.role,
                    "total_incentive": emp_incentive.total_incentive
                }

        # Summary
        total_records = len(results)
        total_incentives = sum(emp.total_incentive for emp in results)
        summary = Summary(
            total_records=total_records,
            total_incentives=total_incentives,
            top_performer=top_performer
        )

        cursor.close()
        conn.close()

        return {
            "status": True,
            "message": "Detailed incentive results fetched successfully",
            "summary": summary.model_dump(),  # Pydantic v2 dict
            "data": [emp.model_dump() for emp in results]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@results_router.get("/GETdashboard_stats", response_model=DashboardAPIResponse)
def GETdashboard_stats():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # ---------- Fetch all incentive calculations ----------
        cursor.execute("SELECT * FROM incentive_calculations")
        rows = cursor.fetchall()
        if not rows:
            return {"status": True, "data": DashboardResponse(
                total_incentive_calculated=0,
                salesperson_processed=0,
                top_performer=TopPerformer(employee_id=None, total_incentive=0),
                last_calculation_run=None
            )}
        
        # ---------- Load into pandas ----------
        df = pd.DataFrame(rows)
        
        # ---------- Total incentive ----------
        total_incentive_calculated = df['total_incentive'].sum()
        
        # ---------- Salesperson processed ----------
        salesperson_processed = df['employee_id'].nunique()
        
        # ---------- Top performer ----------
        top_df = df.groupby('employee_id')['total_incentive'].sum().reset_index()
        top_df = top_df.sort_values('total_incentive', ascending=False).head(1)
        if not top_df.empty:
            top_performer = TopPerformer(
                employee_id=top_df.iloc[0]['employee_id'],
                total_incentive=float(top_df.iloc[0]['total_incentive'])
            )
        else:
            top_performer = TopPerformer(employee_id=None, total_incentive=0)
        
        # ---------- Last calculation run ----------
        df['calculation_date'] = pd.to_datetime(df['calculation_date'])
        last_calculation_run = df['calculation_date'].max()
        
        return {
            "status": True,
            "data": DashboardResponse(
                total_incentive_calculated=float(total_incentive_calculated),
                salesperson_processed=int(salesperson_processed),
                top_performer=top_performer,
                last_calculation_run=last_calculation_run
            )
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()
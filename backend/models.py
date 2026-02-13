from pydantic import BaseModel, Field
from datetime import date,datetime
from typing import List, Optional, Dict, Any

class SalesRow(BaseModel):
    employee_id: str = Field(..., description="Employee ID of the salesperson")
    branch: str = Field(..., description="Branch name")
    role: str = Field(..., description="Employee role")
    vehicle_model: str = Field(..., description="Vehicle model sold")
    vehicle_type: str = Field(..., description="Vehicle type sold")
    quantity: int = Field(..., ge=1, description="Number of units sold")
    sale_date: date = Field(..., description="Date of sale")

class StructuredRuleRow(BaseModel):
    rule_id: str
    role: str
    vehicle_type: str
    min_units: int
    max_units: int
    incentive_amount_inr: float
    bonus_per_unit_inr: float
    valid_from: date
    valid_to: date
    rule_type: str

class AdHocSchemeRow(BaseModel):
    scheme_name: str
    description: str
    applicable_roles: str
    valid_from: date
    valid_to: date

class IncentiveCalculationRequest(BaseModel):
    period: str  # "2025-09"

# ----------------------------
# Ad-Hoc Details Model
# ----------------------------
class AdHocDetail(BaseModel):
    scheme_name: str
    condition: str
    amount: float

# ----------------------------
# Incentive Details Model
# ----------------------------
class IncentiveDetails(BaseModel):
    structured: List[Dict[str, Any]] = []
    ad_hoc: List[AdHocDetail] = []

# ----------------------------
# Employee Incentive Model
# ----------------------------
class EmployeeIncentive(BaseModel):
    employee_id: str
    branch: str
    role: str
    total_units: int
    structured_incentive: float
    adhoc_incentive: float
    total_incentive: float
    status: str
    details: IncentiveDetails

# ----------------------------
# Top Performer Model
# ----------------------------
class TopPerformer(BaseModel):
    employee_id: str = ""
    branch: str = ""
    role: str = ""
    total_incentive: float = 0.0

# ----------------------------
# Summary Model for GETincentiveresults
# ----------------------------
class Summary(BaseModel):
    total_records: int
    total_incentives: float
    top_performer: Optional[Dict[str, Any]] = None  # Nested dict for Pydantic v2

# ----------------------------
# Incentive Response Model
# ----------------------------
class IncentiveResponse(BaseModel):
    status: bool
    message: str
    summary: Summary
    data: List[EmployeeIncentive]

# ----------------------------
# Dashboard Response Models
# ----------------------------
class DashboardResponse(BaseModel):
    total_incentive_calculated: float
    salesperson_processed: int
    top_performer: TopPerformer
    last_calculation_run: Optional[datetime] = None

class DashboardAPIResponse(BaseModel):
    status: bool
    data: DashboardResponse

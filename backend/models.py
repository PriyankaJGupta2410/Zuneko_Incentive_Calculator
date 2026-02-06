from pydantic import BaseModel, Field
from datetime import date
from typing import Optional,List

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

class EmployeeIncentive(BaseModel):
    employee_id: str
    branch: str
    role: str
    total_units: int
    structured_incentive: float
    adhoc_incentive: float
    total_incentive: float
    status: str

class IncentiveResponse(BaseModel):
    status: bool
    message: str
    data: List[EmployeeIncentive]

class CalculationResultSchema(BaseModel):
    employee_id: str
    period_month: str
    total_incentive: float
    breakdown_json: str
    status: str

    class Config:
        from_attributes = True


class CalculationStatsSchema(BaseModel):
    total_incentive: float
    total_salespeople: int
    avg_incentive: float
    top_performer: Optional[str]
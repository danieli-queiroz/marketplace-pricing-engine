from fastapi import APIRouter
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from typing import Optional
from pricing_service import PricingCalculatorService

router = APIRouter()

class PricingRequest(BaseModel):
    product_cost: float
    packaging_cost: float
    current_sale_price: Optional[float] = 0.0
    desired_margin: Optional[float] = 0.0
    tax_percent: float = 0.0
    ads_investment_percent: float = 0.0
    listing_type: str = "premium"
    logistics_type: str = "padrao"
    weight_kg: float = 0.5
    is_cpf: bool = False                
    orders_last_90_days: int = 0        
    use_free_shipping: bool = True      
    shein_days_since_registration: int = 999 

@router.post("/pricing-calculator/calculate", tags=["calculate"])
async def calculate(payload: PricingRequest):
    service = PricingCalculatorService()
    result = service.calculate_price(payload)
    return ORJSONResponse(content={"success": True, "data": result})
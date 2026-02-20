from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    RED = "RED"       
    ORANGE = "ORANGE" 
    GREEN = "GREEN"   

class Family(BaseModel):
    id: int
    name: str

class Substance(BaseModel):
    id: int
    name: str
    families: List[Family] = []

class BrandSubstance(BaseModel):
    substance: Substance
    dosage: Optional[str] = None

class Brand(BaseModel):
    id: int
    cis: str
    name: str
    administration_route: Optional[str] = None
    is_otc: bool
    composition: List[BrandSubstanceInfo] = []

class Rule(BaseModel):
    id: int
    question_code: str
    risk_level: RiskLevel
    advice: str
    
    family_id: Optional[int] = None
    substance_id: Optional[int] = None
    
    filter_route: Optional[str] = None
    filter_polymedication: bool = False
    filter_gender: Optional[str] = None
    age_min: Optional[int] = None
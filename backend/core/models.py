from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class RiskLevel(int, Enum):
    LEVEL_1 = 1  
    LEVEL_2 = 2  
    LEVEL_3 = 3  
    LEVEL_4 = 4  

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
    composition: List[BrandSubstance] = []

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
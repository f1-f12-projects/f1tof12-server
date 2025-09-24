from fastapi import HTTPException
from typing import TYPE_CHECKING
from scripts.db.database_factory import get_database

if TYPE_CHECKING:
    from .api import RequirementCreate

def validate_requirement_fields(requirement: 'RequirementCreate'):
    if not requirement.key_skill.strip():
        raise HTTPException(status_code=400, detail="Key skill is required")
    if not requirement.jd.strip():
        raise HTTPException(status_code=400, detail="JD is required")

    if not requirement.experience_level.strip():
        raise HTTPException(status_code=400, detail="Experience level is required")
    if not requirement.location.strip():
        raise HTTPException(status_code=400, detail="Location is required")
    
    # Check if company exists and is active
    db = get_database()
    companies = db.list_companies()
    company = next((c for c in companies if c['id'] == requirement.company_id), None)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if company['status'] != 'active':
        raise HTTPException(status_code=400, detail="Company is not active")
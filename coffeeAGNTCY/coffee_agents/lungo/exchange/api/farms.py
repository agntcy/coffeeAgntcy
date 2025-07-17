# File: coffeeAGNTCY/coffee_agents/lungo/exchange/api/badge_validation.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from exchange.utils.identity_utils import farm_client_id_map

router = APIRouter()

class ToggleBadgeRequest(BaseModel):
  farm_name: str

@router.post("/farms/toggle-badge")
async def toggle_badge(request: ToggleBadgeRequest):
  """
  Toggles the badge validation for a specific farm by appending or removing '-invalid' in the client_id.

  Args:
      request (ToggleBadgeRequest): Contains the farm name.

  Returns:
      dict: A message indicating the updated client_id.

  Raises:
      HTTPException: 404 if the farm is not found.
  """
  farm_name = request.farm_name

  if farm_name not in farm_client_id_map:
    raise HTTPException(status_code=404, detail=f"Farm '{farm_name}' not found.")

  current_client_id = farm_client_id_map[farm_name]
  if current_client_id.endswith("-invalid"):
    farm_client_id_map[farm_name] = current_client_id[:-8]  # Remove '-invalid'
  else:
    farm_client_id_map[farm_name] = current_client_id + "-invalid"  # Add '-invalid'

  return {"farm_name": farm_name, "client_id": farm_client_id_map[farm_name]}
# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter, HTTPException
import asyncio
import logging

from config.config import IDENTITY_API_KEY, IDENTITY_API_SERVER_URL
from services.identity_service_impl import IdentityServiceImpl

logger = logging.getLogger(__name__)

# Initialize the identity service with API key and base URL
identity_service = IdentityServiceImpl(
  api_key=IDENTITY_API_KEY,
  base_url=IDENTITY_API_SERVER_URL,
)

def normalize_slug(value: str) -> str:
  """
  Normalize a string into a slug-friendly format.
  Converts the string to lowercase, trims whitespace, and replaces spaces with hyphens.

  Args:
      value (str): The input string to normalize.

  Returns:
      str: The normalized slug.
  """
  return value.lower().strip().replace(" ", "-")

def create_apps_router():
  """
  Create a FastAPI router for managing app-related endpoints.

  Returns:
      APIRouter: A router with endpoints for fetching app policies and badges.
  """
  router = APIRouter(prefix="/identity-apps", tags=["identity-apps"])

  async def resolve_app_by_slug(slug: str):
    """
    Resolve an app by its slug or ID. If no match is found, raises an HTTP 404 error.

    Args:
        slug (str): The slug or ID of the app to resolve.

    Returns:
        IdentityServiceApp: The resolved app object.

    Raises:
        HTTPException: 404 if no app matches the slug, 500 if fetching apps fails.
    """
    slug = normalize_slug(slug)
    try:
      apps = await asyncio.to_thread(identity_service.get_all_apps)
    except ValueError as e:
      logger.error(f"Error fetching apps: {e}")
      raise HTTPException(status_code=500, detail="Unable to fetch apps from the identity service.")
    for app in apps.apps:
      if slug == normalize_slug(app.name) or slug == app.id:
        return app
    logger.warning(f"No app found for slug: {slug}")
    raise HTTPException(status_code=404, detail=f"No app found for slug '{slug}'.")

  @router.get("/{slug}/policies", summary="List policies for an app")
  async def get_policies_for_app(slug: str):
    """
    Retrieve policies assigned to the app identified by the given slug.

    Args:
        slug (str): The slug or ID of the app.

    Returns:
        dict: A dictionary containing the app details and its associated policies.

    Raises:
        HTTPException: 500 if the identity service API key is missing or an error occurs.
    """
    if not identity_service.api_key:
      raise HTTPException(status_code=500, detail="Identity service API key is missing.")
    app = await resolve_app_by_slug(slug)
    try:
      policies_model = await identity_service.list_policies()
      filtered_policies = [p for p in policies_model.policies if p.assignedTo == app.id]
      logger.info(f"Resolved slug '{slug}' to app '{app.id}', found {len(filtered_policies)} policies.")
      return {
        "app": {
          "id": app.id,
          "name": app.name,
          "slug": normalize_slug(app.name),
          "type": app.type,
          "status": app.status,
        },
        "policies": [policy.dict() for policy in filtered_policies],
      }
    except ValueError as e:
      logger.error(f"Error fetching policies for app '{app.id}': {e}")
      raise HTTPException(status_code=500, detail="Failed to fetch policies from the identity service.")
    except Exception as e:
      logger.exception(f"Unexpected error: {e}")
      raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching policies.")

  @router.get("/{slug}/badge", summary="Get badge for an app")
  async def get_badge_for_app(slug: str):
    """
    Retrieve the badge for the app identified by the given slug.

    Args:
        slug (str): The slug or ID of the app.

    Returns:
        dict: A dictionary containing the app details and its badge.

    Raises:
        HTTPException: 500 if the identity service API key is missing or an error occurs.
    """
    if not identity_service.api_key:
      raise HTTPException(status_code=500, detail="Identity service API key is missing.")
    app = await resolve_app_by_slug(slug)
    try:
      badge = await asyncio.to_thread(identity_service.get_badge_for_app, app.id)
      logger.info(f"Badge retrieved for app '{app.id}' via slug '{slug}'.")
      return {
        "app": {
          "id": app.id,
          "name": app.name,
          "slug": normalize_slug(app.name),
          "type": app.type,
          "status": app.status,
        },
        "badge": badge.dict(),
      }
    except ValueError as e:
      logger.error(f"Error fetching badge for app '{app.id}': {e}")
      raise HTTPException(status_code=500, detail="Failed to fetch badge from the identity service.")
    except Exception as e:
      logger.exception(f"Unexpected error: {e}")
      raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching the badge.")

  return router
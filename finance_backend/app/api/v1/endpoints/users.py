from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from beanie import PydanticObjectId

from app.api.dependencies import allow_admin, allow_all_roles, get_current_user
from app.models.user import User, Role
from app.schemas.user import UserResponse, RoleUpdate, StatusUpdate

router = APIRouter()

@router.get("/me", response_model=UserResponse, dependencies=[Depends(allow_all_roles)])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(allow_admin)])
async def list_users():
    """List all users (Admin only)."""
    return await User.find_all().sort(-User.created_at).to_list()

@router.patch("/{user_id}/role", response_model=UserResponse, dependencies=[Depends(allow_admin)])
async def update_user_role(user_id: PydanticObjectId, data: RoleUpdate, current_user: User = Depends(get_current_user)):
    """Change a user's role (Admin only). Cannot demote yourself."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == current_user.id and data.role != Role.admin:
        raise HTTPException(status_code=400, detail="Admins cannot demote themselves")

    user.role = data.role
    await user.save()
    return user

@router.patch("/{user_id}/status", response_model=UserResponse, dependencies=[Depends(allow_admin)])
async def update_user_status(user_id: PydanticObjectId, data: StatusUpdate, current_user: User = Depends(get_current_user)):
    """Deactivate or Activate a user (Admin only). Cannot deactivate yourself."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == current_user.id and not data.is_active:
        raise HTTPException(status_code=400, detail="Admins cannot deactivate themselves")

    user.is_active = data.is_active
    await user.save()
    return user

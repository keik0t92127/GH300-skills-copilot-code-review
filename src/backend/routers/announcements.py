"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements() -> List[Dict[str, Any]]:
    """
    Get all announcements sorted by end_date (closest first)
    """
    announcements = []
    for announcement in announcements_collection.find():
        if announcement:
            announcements.append(announcement)
    
    # Sort by end_date descending (most recent first)
    announcements.sort(
        key=lambda x: x.get("end_date", ""),
        reverse=True
    )
    
    return announcements


@router.post("", response_model=Dict[str, Any])
def create_announcement(
    title: str,
    message: str,
    end_date: str,
    start_date: Optional[str] = None,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Create a new announcement - requires teacher authentication
    
    - title: Title of the announcement
    - message: Announcement message content
    - end_date: End date in format YYYY-MM-DD (required)
    - start_date: Start date in format YYYY-MM-DD (optional)
    - teacher_username: Username of authenticated teacher
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Validate dates
    try:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            if start_dt > end_dt:
                raise HTTPException(
                    status_code=400, 
                    detail="Start date cannot be after end date")
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date format. Use YYYY-MM-DD")

    # Generate ID based on current max ID
    all_announcements = announcements_collection.find()
    max_id = max([a.get("_id", 0) for a in all_announcements], default=0)
    new_id = max_id + 1

    # Create announcement
    announcement = {
        "_id": new_id,
        "title": title,
        "message": message,
        "start_date": start_date,
        "end_date": end_date,
        "created_by": teacher_username,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }

    announcements_collection.insert_one(announcement)
    return announcement


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: int,
    title: str,
    message: str,
    end_date: str,
    start_date: Optional[str] = None,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Update an announcement - requires teacher authentication
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Get the announcement
    announcement = announcements_collection.find_one({"_id": announcement_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Validate dates
    try:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            if start_dt > end_dt:
                raise HTTPException(
                    status_code=400, 
                    detail="Start date cannot be after end date")
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date format. Use YYYY-MM-DD")

    # Update announcement
    announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": {
            "title": title,
            "message": message,
            "start_date": start_date,
            "end_date": end_date,
            "updated_by": teacher_username,
            "updated_at": datetime.now().strftime("%Y-%m-%d")
        }}
    )

    # Return updated announcement
    updated = announcements_collection.find_one({"_id": announcement_id})
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Delete an announcement - requires teacher authentication
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Get the announcement
    announcement = announcements_collection.find_one({"_id": announcement_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Delete from the in-memory or MongoDB store
    if hasattr(announcements_collection, 'store'):
        # In-memory storage
        if announcement_id in announcements_collection.store:
            del announcements_collection.store[announcement_id]
    else:
        # MongoDB
        announcements_collection.delete_one({"_id": announcement_id})

    return {"message": f"Announcement {announcement_id} deleted successfully"}

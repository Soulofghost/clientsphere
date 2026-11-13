import uuid
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.database import get_db_connection
from app.schemas import ActivityCreate, ActivityResponse

router = APIRouter(prefix="/activities", tags=["Activities"])

@router.get("", response_model=List[ActivityResponse])
def list_activities(deal_id: Optional[str] = None, contact_id: Optional[str] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM activities"
        conditions = []
        params = []
        if deal_id:
            conditions.append("deal_id = ?")
            params.append(deal_id)
        if contact_id:
            conditions.append("contact_id = ?")
            params.append(contact_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT 100"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [
            ActivityResponse(
                id=r["id"],
                deal_id=r["deal_id"],
                contact_id=r["contact_id"],
                activity_type=r["activity_type"],
                notes=r["notes"],
                created_at=r["created_at"]
            )
            for r in rows
        ]

@router.post("", response_model=ActivityResponse, status_code=201)
def create_activity(activity: ActivityCreate):
    valid_types = ['call', 'meeting', 'email', 'note']
    if activity.activity_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid activity type '{activity.activity_type}'. Allowed: {valid_types}")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contacts WHERE id = ?", (activity.contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Referenced contact does not exist.")

        if activity.deal_id:
            cursor.execute("SELECT id FROM deals WHERE id = ?", (activity.deal_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Referenced deal does not exist.")

        act_id = "act-" + str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO activities (id, deal_id, contact_id, activity_type, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (act_id, activity.deal_id, activity.contact_id, activity.activity_type, activity.notes))
        conn.commit()

        cursor.execute("SELECT * FROM activities WHERE id = ?", (act_id,))
        row = cursor.fetchone()
        return ActivityResponse(
            id=row["id"],
            deal_id=row["deal_id"],
            contact_id=row["contact_id"],
            activity_type=row["activity_type"],
            notes=row["notes"],
            created_at=row["created_at"]
        )

@router.delete("/{activity_id}")
def delete_activity(activity_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        conn.commit()
        return {"status": "deleted", "id": activity_id}

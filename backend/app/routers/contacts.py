import uuid
from fastapi import APIRouter, HTTPException
from typing import List
from app.database import get_db_connection
from app.schemas import ContactCreate, ContactResponse

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("", response_model=List[ContactResponse])
def list_contacts():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts ORDER BY name ASC")
        rows = cursor.fetchall()
        return [
            ContactResponse(
                id=r["id"],
                name=r["name"],
                email=r["email"],
                company=r["company"],
                role=r["role"],
                phone=r["phone"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ) for r in rows
        ]

@router.post("", response_model=ContactResponse, status_code=201)
def create_contact(contact: ContactCreate):
    contact_id = "ct-" + str(uuid.uuid4())[:8]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO contacts (id, name, email, company, role, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (contact_id, contact.name, contact.email, contact.company, contact.role or "Stakeholder", contact.phone))
            conn.commit()
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(status_code=400, detail="A contact with this email address already exists.")
            raise HTTPException(status_code=500, detail=str(e))

        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        saved = cursor.fetchone()
        return ContactResponse(
            id=saved["id"],
            name=saved["name"],
            email=saved["email"],
            company=saved["company"],
            role=saved["role"],
            phone=saved["phone"],
            created_at=saved["created_at"],
            updated_at=saved["updated_at"]
        )

@router.get("/{contact_id}")
def get_contact_detail(contact_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        cursor.execute("SELECT * FROM deals WHERE contact_id = ? ORDER BY value DESC", (contact_id,))
        deals = cursor.fetchall()

        cursor.execute("SELECT * FROM activities WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
        activities = cursor.fetchall()

        return {
            "contact": dict(contact),
            "deals": [dict(d) for d in deals],
            "activities": [dict(a) for a in activities]
        }

@router.delete("/{contact_id}")
def delete_contact(contact_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        return {"status": "deleted", "id": contact_id}

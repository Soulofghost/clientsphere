import uuid
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.database import get_db_connection
from app.schemas import DealCreate, DealUpdate, DealResponse, PipelineForecastResponse
from app.engine.forecast import get_default_probability, compute_weighted_value, compute_pipeline_metrics

router = APIRouter(prefix="/deals", tags=["Deals"])

@router.get("", response_model=List[DealResponse])
def list_deals(stage: Optional[str] = None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT d.*, c.name as contact_name, c.company as contact_company
            FROM deals d
            LEFT JOIN contacts c ON d.contact_id = c.id
        """
        params = []
        if stage and stage != "ALL":
            query += " WHERE d.stage = ?"
            params.append(stage)
        query += " ORDER BY d.value DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            w_val = compute_weighted_value(r["value"], r["probability"])
            result.append(DealResponse(
                id=r["id"],
                contact_id=r["contact_id"],
                contact_name=r["contact_name"],
                contact_company=r["contact_company"],
                title=r["title"],
                value=r["value"],
                stage=r["stage"],
                probability=r["probability"],
                expected_close=r["expected_close"],
                weighted_value=w_val,
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        return result

@router.post("", response_model=DealResponse, status_code=201)
def create_deal(deal: DealCreate):
    deal_id = "deal-" + str(uuid.uuid4())[:8]
    stage = deal.stage or "qualified"
    probability = deal.probability if deal.probability is not None else get_default_probability(stage)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contacts WHERE id = ?", (deal.contact_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Assigned contact does not exist.")

        cursor.execute("""
            INSERT INTO deals (id, contact_id, title, value, stage, probability, expected_close)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (deal_id, deal.contact_id, deal.title, deal.value, stage, probability, deal.expected_close))

        # Log creation activity
        act_id = "act-" + str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO activities (id, deal_id, contact_id, activity_type, notes)
            VALUES (?, ?, ?, 'note', ?)
        """, (act_id, deal_id, deal.contact_id, f"Deal initialized in stage '{stage}' with value ${deal.value:,.2f}."))

        conn.commit()

        cursor.execute("""
            SELECT d.*, c.name as contact_name, c.company as contact_company
            FROM deals d
            LEFT JOIN contacts c ON d.contact_id = c.id
            WHERE d.id = ?
        """, (deal_id,))
        saved = cursor.fetchone()
        return DealResponse(
            id=saved["id"],
            contact_id=saved["contact_id"],
            contact_name=saved["contact_name"],
            contact_company=saved["contact_company"],
            title=saved["title"],
            value=saved["value"],
            stage=saved["stage"],
            probability=saved["probability"],
            expected_close=saved["expected_close"],
            weighted_value=compute_weighted_value(saved["value"], saved["probability"]),
            created_at=saved["created_at"],
            updated_at=saved["updated_at"]
        )

@router.patch("/{deal_id}/stage", response_model=DealResponse)
def update_deal_stage(deal_id: str, new_stage: str):
    valid_stages = ['qualified', 'meeting', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
    if new_stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage '{new_stage}'.")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Deal not found.")

        old_stage = existing["stage"]
        new_prob = get_default_probability(new_stage)

        cursor.execute("""
            UPDATE deals
            SET stage = ?, probability = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_stage, new_prob, deal_id))

        # Log transition activity
        act_id = "act-" + str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO activities (id, deal_id, contact_id, activity_type, notes)
            VALUES (?, ?, ?, 'note', ?)
        """, (act_id, deal_id, existing["contact_id"], f"Deal advanced from '{old_stage}' to '{new_stage}' (Probability: {new_prob}%)."))

        conn.commit()

        cursor.execute("""
            SELECT d.*, c.name as contact_name, c.company as contact_company
            FROM deals d
            LEFT JOIN contacts c ON d.contact_id = c.id
            WHERE d.id = ?
        """, (deal_id,))
        updated = cursor.fetchone()
        return DealResponse(
            id=updated["id"],
            contact_id=updated["contact_id"],
            contact_name=updated["contact_name"],
            contact_company=updated["contact_company"],
            title=updated["title"],
            value=updated["value"],
            stage=updated["stage"],
            probability=updated["probability"],
            expected_close=updated["expected_close"],
            weighted_value=compute_weighted_value(updated["value"], updated["probability"]),
            created_at=updated["created_at"],
            updated_at=updated["updated_at"]
        )

@router.delete("/{deal_id}")
def delete_deal(deal_id: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
        conn.commit()
        return {"status": "deleted", "id": deal_id}

@router.get("/metrics/forecast", response_model=PipelineForecastResponse)
def get_forecast():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM deals")
        deals = [dict(r) for r in cursor.fetchall()]
        metrics = compute_pipeline_metrics(deals)
        return PipelineForecastResponse(**metrics)

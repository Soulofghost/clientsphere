import os
import pytest
from fastapi.testclient import TestClient

# Use an in-memory or test database file for isolation
os.environ["CLIENTSPHERE_DB"] = "test_clientsphere.db"

from app.main import app
from app.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    if os.path.exists("test_clientsphere.db"):
        os.remove("test_clientsphere.db")
    init_db()
    yield
    if os.path.exists("test_clientsphere.db"):
        try:
            os.remove("test_clientsphere.db")
        except Exception:
            pass

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ClientSphere CRM"

def test_contact_lifecycle(client):
    # Create contact
    contact_payload = {
        "name": "Dr. Aris Vance",
        "email": "aris.vance@quantumcore.dev",
        "company": "QuantumCore Labs",
        "role": "Chief Scientist",
        "phone": "+1 415-888-0199"
    }
    res = client.post("/api/v1/contacts", json=contact_payload)
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == "Dr. Aris Vance"
    assert created["company"] == "QuantumCore Labs"
    contact_id = created["id"]

    # Prevent duplicate email
    res_dup = client.post("/api/v1/contacts", json=contact_payload)
    assert res_dup.status_code == 400

    # List contacts
    res_list = client.get("/api/v1/contacts")
    assert res_list.status_code == 200
    contacts = res_list.json()
    assert any(c["id"] == contact_id for c in contacts)

def test_deal_and_forecast_lifecycle(client):
    # Fetch an existing contact
    contacts = client.get("/api/v1/contacts").json()
    target_contact = contacts[0]

    # Create new deal
    deal_payload = {
        "contact_id": target_contact["id"],
        "title": "Quantum Compute Cluster Integration",
        "value": 150000.0,
        "stage": "qualified",
        "expected_close": "2026-12-31"
    }
    res = client.post("/api/v1/deals", json=deal_payload)
    assert res.status_code == 201
    deal = res.json()
    assert deal["title"] == "Quantum Compute Cluster Integration"
    assert deal["probability"] == 20
    assert deal["weighted_value"] == 30000.0
    deal_id = deal["id"]

    # Advance stage to negotiation
    res_stage = client.patch(f"/api/v1/deals/{deal_id}/stage?new_stage=negotiation")
    assert res_stage.status_code == 200
    updated_deal = res_stage.json()
    assert updated_deal["stage"] == "negotiation"
    assert updated_deal["probability"] == 80
    assert updated_deal["weighted_value"] == 120000.0

    # Verify forecast update
    res_forecast = client.get("/api/v1/deals/metrics/forecast")
    assert res_forecast.status_code == 200
    forecast = res_forecast.json()
    assert forecast["total_pipeline_value"] > 0
    assert forecast["weighted_pipeline_value"] > 0

def test_activity_logging(client):
    contacts = client.get("/api/v1/contacts").json()
    deals = client.get("/api/v1/deals").json()
    c_id = contacts[0]["id"]
    d_id = deals[0]["id"]

    activity_payload = {
        "deal_id": d_id,
        "contact_id": c_id,
        "activity_type": "meeting",
        "notes": "Discussed Q4 rollout schedule, security compliance and multi-region failover."
    }
    res = client.post("/api/v1/activities", json=activity_payload)
    assert res.status_code == 201
    act = res.json()
    assert act["activity_type"] == "meeting"
    assert act["notes"] == activity_payload["notes"]

    # Filter activities by deal
    res_list = client.get(f"/api/v1/activities?deal_id={d_id}")
    assert res_list.status_code == 200
    acts = res_list.json()
    assert any(a["id"] == act["id"] for a in acts)

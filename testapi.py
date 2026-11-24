import os
import sys

os.environ["BLOCK911_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_block911.db")
if os.path.exists(os.environ["BLOCK911_DB"]):
    os.remove(os.environ["BLOCK911_DB"])

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
from main import app

with TestClient(app) as c:
    assert c.get("/api/health").json()["status"] == "online"
    t = c.get("/api/transactions").json()
    assert len(t) == 4 and t[0]["id"] == "TXN-8942", t[0]["id"]
    s = c.get("/api/stats").json()
    print("Initial stats:", s)
    assert s["active_rings"] == 1 and s["open_cases"] == 3

    # Validation check
    assert c.post("/api/transactions", json={"email": "bad", "amount": 5}).status_code == 422
    assert c.post("/api/transactions", json={"email": "a@b.co", "amount": -1}).status_code == 422

    # High-risk transaction check
    body = {
        "customer_name": "Amit Kapoor",
        "email": "Amit.K@yopmail.com",
        "amount": 2000,
        "proxy_detected": True,
        "device_spoofed": True,
        "velocity_10m": 8,
    }
    r = c.post("/api/transactions", json=body)
    assert r.status_code == 201
    r = r.json()
    print("Created high-risk txn:", r["id"], r["risk_score"], r["status"])
    assert r["risk_score"] == 98 and r["id"] == "TXN-8943"

    # Low-risk transaction check
    ok = c.post(
        "/api/transactions",
        json={"customer_name": "Sana Qureshi", "email": "sana.q@gmail.com", "amount": 40},
    ).json()
    assert ok["status"] == "Approved" and ok["risk_score"] == 15

    # Resolve fraud -> blacklist -> repeat penalty
    res = c.post(
        "/api/transactions/TXN-8943/resolve",
        json={"verdict": "Fraud", "note": "confirmed"},
    ).json()
    assert res["investigation_status"] == "Declined & Blacklisted"
    assert c.get("/api/blacklist").json() == ["amit.k@yopmail.com"]

    again = c.post(
        "/api/transactions",
        json={"customer_name": "Amit Kapoor", "email": "amit.k@yopmail.com", "amount": 10},
    ).json()
    assert "blacklist" in " ".join(again["heuristics"]).lower()
    assert again["customer_id"] == r["customer_id"]

    assert c.post("/api/transactions/TXN-8943/resolve", json={"verdict": "Safe"}).status_code == 409
    assert c.post("/api/transactions/NOPE/resolve", json={"verdict": "Safe"}).status_code == 404

    g = c.get("/api/graph").json()
    assert any(n["id"] == "DEV-EMULATED-X86" for n in g["nodes"])
    assert len(c.get("/api/transactions?status=Declined").json()) >= 3
    assert len(c.get("/api/transactions?q=rahul").json()) == 1
    print("ALL TESTS PASSED:", c.get("/api/stats").json())

if os.path.exists(os.environ["BLOCK911_DB"]):
    os.remove(os.environ["BLOCK911_DB"])
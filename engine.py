"""Block911 scoring engine - pure Python, no web or database code."""

from typing import Any, Dict, List, Set, Tuple

SETTINGS: Dict[str, int] = {"approve_cutoff": 30, "challenge_cutoff": 75}

DISPOSABLE_EMAIL_DOMAINS: Set[str] = {
    "mailinator.com",
    "guerrillamail.com",
    "tempmail.com",
    "10minutemail.com",
    "yopmail.com",
    "trashmail.com",
}


def score_payload(payload: Dict[str, Any], blacklist: Set[str]) -> Dict[str, Any]:
    """Return score, decision and triggered rules for a raw payload."""
    score = 15
    heuristics: List[str] = []

    amount = float(payload.get("amount", 0.0))
    if amount > 1000.0:
        score += 22
        heuristics.append("High transaction ticket (>$1,000 / high value)")

    if payload.get("proxy_detected"):
        score += 35
        heuristics.append("Tor exit node / datacenter proxy detected")

    velocity = int(payload.get("velocity_10m", 1))
    if velocity > 4:
        score += 24
        heuristics.append(f"High 10m velocity anomaly: {velocity} events")

    if payload.get("device_spoofed"):
        score += 20
        heuristics.append("UserAgent & WebGL canvas mismatch (fingerprint spoof)")

    email = str(payload.get("email", "")).lower()
    domain = email.split("@")[-1] if "@" in email else ""
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        score += 12
        heuristics.append(f"Disposable e-mail domain ({domain})")

    if email and email in blacklist:
        score += 40
        heuristics.append("Customer e-mail is on the blacklist")

    score = min(max(score, 8), 98)
    status, investigation = decide(score)
    return {
        "risk_score": score,
        "status": status,
        "investigation_status": investigation,
        "heuristics": heuristics,
    }


def decide(score: int) -> Tuple[str, str]:
    if score >= SETTINGS["challenge_cutoff"]:
        return "Declined", "Open Triage"
    if score >= SETTINGS["approve_cutoff"]:
        return "Challenged", "Challenged (3DS OTP Pending)"
    return "Approved", "Safe"
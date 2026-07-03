"""TrustLedger + Sentinel — settlement audit trail and anti-fraud.

Every market event (bid, allocation, verification, payment) is hash-chained
into an append-only ledger: block N stores SHA-256(block N-1 hash + payload),
so any tampering is detectable by replaying the chain. No tokens, no crypto
payments — this is audit infrastructure; settlement itself is VND rails.

Sentinel screens every bid BEFORE money moves: a bid above the household's
physically possible surplus (panel size x irradiance) is rejected and logged.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


@dataclass
class TrustLedger:
    blocks: list = field(default_factory=list)

    def append(self, event_type: str, payload: dict) -> dict:
        prev_hash = self.blocks[-1]["hash"] if self.blocks else "GENESIS"
        body = {
            "n": len(self.blocks),
            "type": event_type,
            "payload": payload,
            "prev": prev_hash,
        }
        digest = hashlib.sha256(
            (prev_hash + json.dumps(body, sort_keys=True, default=str)).encode()
        ).hexdigest()
        block = {**body, "hash": digest}
        self.blocks.append(block)
        return block

    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for b in self.blocks:
            body = {k: b[k] for k in ("n", "type", "payload", "prev")}
            digest = hashlib.sha256(
                (prev + json.dumps(body, sort_keys=True, default=str)).encode()
            ).hexdigest()
            if digest != b["hash"] or b["prev"] != prev:
                return False
            prev = b["hash"]
        return True


@dataclass
class Sentinel:
    ledger: TrustLedger

    def screen_bid(self, hid: int, bid_kw: float, physical_cap_kw: float):
        """Return (ok, message). Fraudulent bids are blocked and logged."""
        if bid_kw <= physical_cap_kw + 1e-6:
            return True, "OK"
        msg = (
            f"BLOCKED: household H{hid:02d} bid {bid_kw:.1f} kW but its physical "
            f"maximum this window is {physical_cap_kw:.1f} kW. "
            "Bid rejected before auction; payment impossible."
        )
        self.ledger.append(
            "fraud_blocked",
            {"hid": hid, "bid_kw": bid_kw, "cap_kw": round(physical_cap_kw, 3)},
        )
        return False, msg

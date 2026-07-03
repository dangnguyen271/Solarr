"""HeadRoom Auction — fair allocation of scarce export headroom.

Each 15-minute window, PV households bid their forecast-capped surplus.
A small MILP (PuLP/CBC) accepts bids to maximise renewable utilisation,
price merit and fairness credits, subject to the hard safety constraint:

    sum(accepted export) <= SAFETY_MARGIN * forecast headroom

Fairness: every rejection earns a credit that raises the household's
priority in later windows, so nobody is persistently excluded by pure
price competition. Every decision carries a one-line explanation.
A greedy fallback guarantees the demo never stalls if CBC misbehaves.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

try:
    import pulp

    HAS_PULP = True
except ImportError:  # pragma: no cover
    HAS_PULP = False

SAFETY_MARGIN = 0.90
BASE_PRICE_VND = 700.0        # Decree-58 reference buyback, VND/kWh
FLEX_PREMIUM_VND = 250.0      # FlexMatch demand premium in the solar window


@dataclass
class Bid:
    hid: int
    kw: float                  # offered export power for the window
    cap_kw: float              # physical/forecast cap (Sentinel checks this)
    fairness_credit: int = 0


@dataclass
class Allocation:
    hid: int
    accepted_kw: float
    reason: str


@dataclass
class AuctionEngine:
    n_households: int
    fairness_credits: np.ndarray = field(init=False)
    consecutive_rejects: np.ndarray = field(init=False)
    max_consecutive_rejects: int = 0

    def __post_init__(self):
        self.fairness_credits = np.zeros(self.n_households)
        self.consecutive_rejects = np.zeros(self.n_households, dtype=int)

    # ------------------------------------------------------------------ #
    def clear_window(self, bids: list[Bid], headroom_kw: float) -> list[Allocation]:
        """Clear one 15-minute window; updates fairness state."""
        budget = SAFETY_MARGIN * max(headroom_kw, 0.0)
        live = [b for b in bids if b.kw > 1e-6]
        if not live:
            return []

        total_offered = sum(b.kw for b in live)
        if total_offered <= budget:
            allocations = [
                Allocation(b.hid, b.kw, "Accepted in full — headroom sufficient.")
                for b in live
            ]
            self._update_fairness(live, {b.hid: b.kw for b in live})
            return allocations

        weights = {
            b.hid: 1.0 + 0.15 * self.fairness_credits[b.hid] for b in live
        }
        accepted = (
            self._clear_milp(live, budget, weights)
            if HAS_PULP
            else self._clear_greedy(live, budget, weights)
        ) or self._clear_greedy(live, budget, weights)

        allocations = []
        for b in live:
            got = accepted.get(b.hid, 0.0)
            if got >= b.kw - 1e-6:
                reason = "Accepted in full."
            elif got > 1e-6:
                reason = f"Partially accepted ({got:.2f} of {b.kw:.2f} kW) — feeder headroom binding."
            else:
                reason = (
                    "Declined this window — headroom exhausted. "
                    f"Priority credit granted (now {int(self.fairness_credits[b.hid]) + 1})."
                )
            allocations.append(Allocation(b.hid, got, reason))
        self._update_fairness(live, accepted)
        return allocations

    # ------------------------------------------------------------------ #
    def _clear_milp(self, bids, budget, weights):
        try:
            prob = pulp.LpProblem("headroom_auction", pulp.LpMaximize)
            x = {
                b.hid: pulp.LpVariable(f"x_{b.hid}", lowBound=0, upBound=b.kw)
                for b in bids
            }
            # small binary bonus for full acceptance keeps allocations tidy
            y = {
                b.hid: pulp.LpVariable(f"y_{b.hid}", cat="Binary") for b in bids
            }
            prob += pulp.lpSum(weights[b.hid] * x[b.hid] + 0.01 * y[b.hid] for b in bids)
            prob += pulp.lpSum(x.values()) <= budget
            for b in bids:
                prob += x[b.hid] >= b.kw * y[b.hid] - 1e-6
            prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=5))
            if pulp.LpStatus[prob.status] != "Optimal":
                return None
            return {hid: float(v.value() or 0.0) for hid, v in x.items()}
        except Exception:
            return None

    @staticmethod
    def _clear_greedy(bids, budget, weights):
        remaining = budget
        accepted = {}
        for b in sorted(bids, key=lambda b: -weights[b.hid]):
            take = min(b.kw, remaining)
            accepted[b.hid] = take
            remaining -= take
            if remaining <= 1e-9:
                break
        return accepted

    # ------------------------------------------------------------------ #
    def _update_fairness(self, bids, accepted):
        for b in bids:
            if accepted.get(b.hid, 0.0) > 1e-6:
                self.fairness_credits[b.hid] = 0
                self.consecutive_rejects[b.hid] = 0
            else:
                self.fairness_credits[b.hid] += 1
                self.consecutive_rejects[b.hid] += 1
        if len(self.consecutive_rejects):
            self.max_consecutive_rejects = max(
                self.max_consecutive_rejects, int(self.consecutive_rejects.max())
            )

"""Rate limits and the spend cap for AI requests."""

from dataclasses import dataclass

from chromasense.core.errors import AiRateLimited, AiSpendCapReached
from chromasense.core.models import AiUsage


@dataclass(frozen=True)
class AiLimits:
    session_limit: int
    ip_limit: int
    spend_cap: float

    def check(self, usage: AiUsage) -> None:
        if usage.session_count >= self.session_limit or usage.ip_count >= self.ip_limit:
            raise AiRateLimited("Too many AI requests. Try again later.")
        if usage.total_cost >= self.spend_cap:
            raise AiSpendCapReached("AI is temporarily unavailable")

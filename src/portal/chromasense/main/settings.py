"""Configuration. This is the only module that reads the environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    retention_hours: float = 24.0
    confusion_threshold: float = 10.0
    purge_interval_seconds: float = 3600.0
    data_dir: str = "/data"
    provider_url: str = ""
    model: str = ""
    api_key: str = field(default="", repr=False)
    cost_per_request: float = 0.0
    rate_limit_session: int = 20
    rate_limit_ip: int = 60
    rate_window_seconds: float = 3600.0
    spend_cap: float = 5.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = os.environ if env is None else env
        defaults = cls()

        def value(name: str, default: str) -> str:
            return source.get(f"CHROMASENSE_{name}", "").strip() or default

        def number(name: str, default: float) -> float:
            return float(value(name, str(default)))

        return cls(
            retention_hours=number("RETENTION_HOURS", defaults.retention_hours),
            confusion_threshold=number("CONFUSION_THRESHOLD", defaults.confusion_threshold),
            purge_interval_seconds=number(
                "PURGE_INTERVAL_SECONDS", defaults.purge_interval_seconds
            ),
            data_dir=value("DATA_DIR", defaults.data_dir),
            provider_url=value("PROVIDER_URL", ""),
            model=value("MODEL", ""),
            api_key=value("API_KEY", ""),
            cost_per_request=number("COST_PER_REQUEST", defaults.cost_per_request),
            rate_limit_session=int(number("RATE_LIMIT_SESSION", defaults.rate_limit_session)),
            rate_limit_ip=int(number("RATE_LIMIT_IP", defaults.rate_limit_ip)),
            rate_window_seconds=number("RATE_WINDOW_SECONDS", defaults.rate_window_seconds),
            spend_cap=number("SPEND_CAP", defaults.spend_cap),
        )

"""Composition root: construct the parts and wire them together."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI

from chromasense.ai_gateway.http_vision_reader import HttpVisionReader
from chromasense.core.policy.ai_limits import AiLimits
from chromasense.core.ports import VisionReader
from chromasense.core.use_cases.answer_question import AnswerQuestion
from chromasense.core.use_cases.export_image import ExportImage
from chromasense.core.use_cases.get_analysis import GetAnalysis
from chromasense.core.use_cases.identify_color import IdentifyColor
from chromasense.core.use_cases.interpret_image import InterpretImage
from chromasense.core.use_cases.process_upload import ProcessUpload
from chromasense.core.use_cases.purge_expired import PurgeExpired, PurgeExpiredRequest
from chromasense.core.use_cases.reanalyze_for_profile import ReanalyzeForProfile
from chromasense.core.use_cases.render_view import RenderView
from chromasense.main.settings import Settings
from chromasense.storage.filesystem_image_store import FilesystemImageStore
from chromasense.storage.sqlite_ai_usage_ledger import SqliteAiUsageLedger
from chromasense.storage.sqlite_interpretation_cache import SqliteInterpretationCache
from chromasense.web_api.app import UseCases, create_app

logger = logging.getLogger("chromasense.main")


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def build_app(settings: Settings, reader: VisionReader | None = None) -> FastAPI:
    clock = SystemClock()
    store = FilesystemImageStore(settings.data_dir)
    threshold = settings.confusion_threshold
    database = Path(settings.data_dir) / "chromasense.sqlite3"
    cache = SqliteInterpretationCache(database)
    ledger = SqliteAiUsageLedger(database, settings.rate_window_seconds)
    limits = AiLimits(settings.rate_limit_session, settings.rate_limit_ip, settings.spend_cap)
    vision_reader = reader or HttpVisionReader(
        settings.provider_url, settings.api_key, settings.model, settings.cost_per_request
    )
    use_cases = UseCases(
        process_upload=ProcessUpload(
            store, clock, threshold, timedelta(hours=settings.retention_hours)
        ),
        get_analysis=GetAnalysis(store),
        reanalyze_for_profile=ReanalyzeForProfile(store, threshold),
        render_view=RenderView(store, threshold),
        identify_color=IdentifyColor(store),
        export_image=ExportImage(store, threshold),
        interpret_image=InterpretImage(store, vision_reader, cache, ledger, limits, clock),
        answer_question=AnswerQuestion(store, vision_reader, cache, ledger, limits, clock),
    )
    purge = PurgeExpired(store, cache, clock)
    return create_app(use_cases, lifespan=_purge_schedule(purge, settings.purge_interval_seconds))


def _purge_schedule(purge: PurgeExpired, interval_seconds: float):
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(_purge_forever(purge, interval_seconds))
        try:
            yield
        finally:
            task.cancel()

    return lifespan


async def _purge_forever(purge: PurgeExpired, interval_seconds: float) -> None:
    while True:
        try:
            await asyncio.to_thread(purge.execute, PurgeExpiredRequest())
        except OSError:
            logger.exception("Purging expired data failed")
        await asyncio.sleep(interval_seconds)

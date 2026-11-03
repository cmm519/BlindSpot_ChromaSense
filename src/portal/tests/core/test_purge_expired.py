from datetime import timedelta

import numpy as np
from fakes import START, FakeClock, FakeInterpretationCache

from chromasense.core.models import ImageRecord
from chromasense.core.use_cases.purge_expired import PurgeExpired, PurgeExpiredRequest
from chromasense.storage.filesystem_image_store import FilesystemImageStore


def test_past_the_expiry_time_the_image_folder_is_removed_from_disk(tmp_path):
    store = FilesystemImageStore(tmp_path)
    image_id = "a" * 32
    record = ImageRecord(image_id, "hash", 2, 2, START, START + timedelta(hours=24))
    store.save(record, b"original", np.zeros((2, 2, 3), dtype=np.uint8))
    folder = tmp_path / "images" / image_id
    assert folder.is_dir()

    clock = FakeClock(START + timedelta(hours=23))
    cache = FakeInterpretationCache()
    use_case = PurgeExpired(store, cache, clock)
    assert use_case.execute(PurgeExpiredRequest()).images_deleted == 0
    assert folder.is_dir()

    clock.current = START + timedelta(hours=24)
    assert use_case.execute(PurgeExpiredRequest()).images_deleted == 1
    assert not folder.exists()
    assert cache.deleted_at == [START + timedelta(hours=23), START + timedelta(hours=24)]

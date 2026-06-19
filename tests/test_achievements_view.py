# tests/test_achievements_view.py
# С70 полировка: пур-хелперы экрана каталога достижений (ui/hub/achievements_view.py).
# Тестируем ТОЛЬКО логику строк/сводки (без pygame-отрисовки): корректная разметка
# выполнено/заперто из meta['achievements'] и счёт X/N.

from core import achievements
from ui.hub.achievements_view import catalog_rows, progress_summary


def test_catalog_rows_count_and_order_match_registry():
    rows = catalog_rows({})
    assert len(rows) == len(achievements.ACHIEVEMENTS)
    # Порядок строк = порядок реестра (стабильность UI).
    assert [r["id"] for r in rows] == [a.id for a in achievements.ACHIEVEMENTS]


def test_empty_meta_all_locked():
    rows = catalog_rows({})
    assert all(r["done"] is False for r in rows)
    assert progress_summary({}) == (0, len(achievements.ACHIEVEMENTS))


def test_none_meta_safe():
    # meta=None не должна падать — экран рисуется и для свежего сейва без меты.
    rows = catalog_rows(None)
    assert len(rows) == len(achievements.ACHIEVEMENTS)
    assert progress_summary(None) == (0, len(achievements.ACHIEVEMENTS))


def test_done_flag_reflects_meta():
    first_id = achievements.ACHIEVEMENTS[0].id
    meta = {"achievements": [first_id]}
    rows = {r["id"]: r for r in catalog_rows(meta)}
    assert rows[first_id]["done"] is True
    # Остальные — заперты.
    assert sum(1 for r in rows.values() if r["done"]) == 1
    assert progress_summary(meta) == (1, len(achievements.ACHIEVEMENTS))


def test_row_carries_reward_and_kind():
    rows = {r["id"]: r for r in catalog_rows({})}
    for a in achievements.ACHIEVEMENTS:
        row = rows[a.id]
        assert row["reward"] == a.grant_id
        assert row["kind"] == a.grant_kind
        assert row["title"] == a.title
        assert row["description"] == a.description

from __future__ import annotations

from engine.registry import NODE_HANDLERS, NODE_SPECS, get_spec


def test_datetime_and_rss_aliases_resolve() -> None:
    assert "DATE_TIME" in NODE_SPECS
    assert "DATETIME" in NODE_SPECS
    assert get_spec("DATETIME").type_id == "DATE_TIME"
    assert NODE_HANDLERS["DATETIME"] is NODE_HANDLERS["DATE_TIME"]

    assert "RSS_READ" in NODE_SPECS
    assert "RSS_FEED_READ" in NODE_SPECS
    assert get_spec("RSS_FEED_READ").type_id == "RSS_READ"
    assert NODE_HANDLERS["RSS_FEED_READ"] is NODE_HANDLERS["RSS_READ"]

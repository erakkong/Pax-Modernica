"""
Unit tests for European map topology and data structure.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "server" / "data"

def test_map_data_integrity():
    map_file = DATA_DIR / "europe_map.json"
    assert map_file.exists()

    data = json.loads(map_file.read_text(encoding="utf-8"))
    provinces = data.get("provinces", [])
    assert len(provinces) >= 50

    province_ids = {p["id"] for p in provinces}
    assert len(province_ids) == len(provinces), "Province IDs must be unique"

    # Check Iceland prominence as specifically requested in section 3
    iceland_provinces = [p for p in provinces if "iceland" in p["id"]]
    assert len(iceland_provinces) >= 2, "Iceland must have prominent provincial representation"

    for p in provinces:
        assert "center" in p and len(p["center"]) == 2
        assert "svg_path" in p and p["svg_path"].startswith("M")
        assert "terrain" in p
        assert "population" in p and p["population"] > 0
        assert "tax_revenue" in p and p["tax_revenue"] > 0

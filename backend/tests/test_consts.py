import pytest
from utils.consts import BASE_MODEL, DEVICE, DB_PATH


class TestConstants:

    def test_base_model_defined(self):
        assert BASE_MODEL is not None
        assert isinstance(BASE_MODEL, str)
        assert len(BASE_MODEL) > 0

    def test_base_model_value(self):
        assert "Qwen" in BASE_MODEL
        assert "VL" in BASE_MODEL

    def test_device_defined(self):
        assert DEVICE is not None
        assert isinstance(DEVICE, str)

    def test_device_valid(self):
        assert DEVICE in ["cuda", "cpu"]

    def test_db_path_defined(self):
        assert DB_PATH is not None
        assert isinstance(DB_PATH, str)
        assert len(DB_PATH) > 0

    def test_db_path_format(self):
        assert DB_PATH.endswith(".duckdb")

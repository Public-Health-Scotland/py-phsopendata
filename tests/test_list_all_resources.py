# tests/test_list_all_resources.py
import os
import re
import importlib
import types
import pytest
import pandas as pd

from phsopendata.list_all_resources import list_all_resources  # <-- change this

def _resolve_target_module():
    """
    Resolve the module object that contains list_all_resources so we can
    monkeypatch its directly imported names (opendata_ua, request_url, requests.get).
    """
    module_name = list_all_resources.__module__
    return importlib.import_module(module_name)


def _fake_api_payload():
    """
    Build a minimal but representative CKAN /package_search response.
    Includes multiple packages and resources to test mapping, filtering, and datetime parsing.
    """
    return {
        "result": {
            "results": [
                {
                    "id": "pkg1",
                    "name": "my-dataset",
                    "resources": [
                        {
                            "name": "European Age-standard Rates",
                            "id": "res1",
                            "package_id": "pkg1",
                            "url": "https://open.example/res1.csv",
                            "last_modified": "2023-01-01T10:20:30.123456",
                        },
                        {
                            "name": "SMR01 Admissions",
                            "id": "res2",
                            "package_id": "pkg1",
                            "url": "https://open.example/res2.csv",
                            "last_modified": "2024-05-05T12:34:56.000000",
                        },
                    ],
                },
                {
                    "id": "pkg2",
                    "name": "Test Dataset Two",
                    "resources": [
                        {
                            "name": "Population - GP list",
                            "id": "res3",
                            "package_id": "pkg2",
                            "url": "https://open.example/res3.csv",
                            "last_modified": "2022-12-31T23:59:59.999999",
                        }
                    ],
                },
            ]
        }
    }


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


@pytest.fixture
def mock_happy_path(monkeypatch):
    """
    Monkeypatch opendata_ua, request_url, and requests.get to avoid live calls.
    """
    target_module = _resolve_target_module()

    # Fake header
    def fake_ua():
        return {"User-Agent": "pytest-opendata-UA"}

    # Fake endpoint builder
    def fake_request_url(name: str) -> str:
        assert name == "package_search"
        return "https://dummy.api/3/action/package_search"

    # Fake requests.get
    def fake_get(url, headers=None, params=None):
        # Assert the function used expected URL and params
        assert url == fake_request_url("package_search")
        assert params == {"q": "*:*", "rows": "32000"}
        assert headers == fake_ua()
        return _FakeResponse(_fake_api_payload())

    monkeypatch.setattr(target_module, "opendata_ua", fake_ua, raising=True)
    monkeypatch.setattr(target_module, "request_url", fake_request_url, raising=True)

    # requests was imported at module level as `requests`; patch it there
    import requests as real_requests
    monkeypatch.setattr(target_module, "requests", types.SimpleNamespace(get=fake_get, exceptions=real_requests.exceptions))

    return True


def test_return_format_columns_and_types(mock_happy_path):
    df = list_all_resources()

    # Type and columns
    assert isinstance(df, pd.DataFrame)
    expected_cols = ["resource_name", "resource_id", "dataset_name", "dataset_id", "url", "last_modified"]
    assert list(df.columns) == expected_cols

    # Row count equals total mocked resources (3)
    assert len(df) == 3

    # last_modified should be datetime64[ns] and floored to seconds
    assert pd.api.types.is_datetime64_ns_dtype(df["last_modified"])
    # Check flooring worked (microseconds dropped)
    row = df.loc[df["resource_id"] == "res1"].iloc[0]
    assert row["last_modified"] == pd.Timestamp("2023-01-01T10:20:30")


def test_filters_dataset_and_resource(mock_happy_path):
    # Dataset regex matches "Test Dataset Two" (case-insensitive)
    # Resource regex matches "Population - GP list" (also case-insensitive)
    df = list_all_resources(dataset_contains="^test\\s+dataset", resource_contains="population")

    assert len(df) == 1
    assert df.iloc[0]["dataset_id"] == "pkg2"
    assert df.iloc[0]["resource_id"] == "res3"
    assert df.iloc[0]["resource_name"] == "Population - GP list"


def test_dataset_filter_warns_on_no_matches(mock_happy_path):
    with pytest.warns(UserWarning, match="No datasets found"):
        df = list_all_resources(dataset_contains="does-not-exist")
    assert df.empty


def test_resource_filter_warns_on_no_matches(mock_happy_path):
    # First narrow to a known dataset; then force no resource matches
    with pytest.warns(UserWarning, match="No resources found"):
        df = list_all_resources(dataset_contains="my-dataset", resource_contains="ZZZ_NO_MATCH")
    assert df.empty


def test_argument_type_errors():
    # dataset_contains must be None or str
    with pytest.raises(ValueError, match="dataset_contains must be None or have string length 1"):
        list_all_resources(dataset_contains=123)

    # resource_contains must be None or str
    with pytest.raises(ValueError, match="resource_contains must be None or have string length 1"):
        list_all_resources(resource_contains=["not", "a", "string"])


def test_requests_exception_raises_systemexit(monkeypatch):
    target_module = _resolve_target_module()

    def fake_ua():
        return {"User-Agent": "pytest-opendata-UA"}

    def fake_request_url(name: str) -> str:
        return "https://dummy.api/3/action/package_search"

    import requests as real_requests

    def fake_get(*args, **kwargs):
        raise real_requests.exceptions.RequestException("boom")

    monkeypatch.setattr(target_module, "opendata_ua", fake_ua, raising=True)
    monkeypatch.setattr(target_module, "request_url", fake_request_url, raising=True)
    monkeypatch.setattr(target_module, "requests", types.SimpleNamespace(get=fake_get, exceptions=real_requests.exceptions))

    with pytest.raises(SystemExit):
        list_all_resources()
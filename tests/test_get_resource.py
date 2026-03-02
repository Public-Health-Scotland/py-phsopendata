import pytest
import pandas as pd
import types
import importlib

from phsopendata.get_resource import get_resource


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def _resolve_mod():
    """Retrieve the module where get_resource is defined so we can patch its imports."""
    return importlib.import_module(get_resource.__module__)


class FakeResponse:
    """Minimal fake requests.Response for mocked API calls."""
    def __init__(self, json_payload, status=200):
        self._json = json_payload
        self.status_code = status

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("HTTP error")


# --------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------

@pytest.fixture
def mock_env(monkeypatch):
    """
    Patches:
        - check_res_id
        - parse_col_select
        - parse_row_filters
        - opendata_ua
        - request_url
        - requests.get
        - get_resource_sql
        - dump_download
    """

    mod = _resolve_mod()

    # Valid res_id only if string "valid-id"
    monkeypatch.setattr(mod, "check_res_id", lambda x: x == "valid-id")

    # echo behaviour
    monkeypatch.setattr(mod, "parse_col_select", lambda cols: cols)
    monkeypatch.setattr(mod, "parse_row_filters", lambda rf: rf)

    # fake user agent
    monkeypatch.setattr(mod, "opendata_ua", lambda: {"User-Agent": "pytest-UA"})

    # request_url builder
    monkeypatch.setattr(
        mod,
        "request_url",
        lambda endpoint: f"https://fake.api/{endpoint}"
    )

    # track calls
    call_log = {"sql": None, "dump": None}

    # fake SQL path
    def fake_sql(sql_query):
        call_log["sql"] = sql_query
        return pd.DataFrame([{"A": 1, "B": 2}])

    # fake dump_download
    def fake_dump(res_id):
        call_log["dump"] = res_id
        return pd.DataFrame([{"X": 10, "Y": 20}])

    monkeypatch.setattr(mod, "get_resource_sql", fake_sql)
    monkeypatch.setattr(mod, "dump_download", fake_dump)

    return call_log


# --------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------

def test_invalid_res_id_raises(monkeypatch):
    mod = _resolve_mod()
    monkeypatch.setattr(mod, "check_res_id", lambda x: False)

    with pytest.raises(ValueError, match="invalid"):
        get_resource("bad-id")


# ---------- SQL PATH -------------------------------------------------

def test_sql_path_simple_filter(mock_env, monkeypatch):
    """When parse_row_filters returns False AND row_filters is not None → SQL used."""

    mod = _resolve_mod()

    # force SQL path behaviour
    monkeypatch.setattr(mod, "parse_row_filters", lambda rf: False)

    df = get_resource("valid-id", row_filters={"Sex": "Female"}, col_select=["Age", "Sex"])

    # verify SQL was used
    assert mock_env["sql"] is not None
    assert 'SELECT "Age","Sex" FROM "valid-id"' in mock_env["sql"]

    # verify returned df from fake_sql
    assert isinstance(df, pd.DataFrame)


def test_sql_path_multi_value_filter(mock_env, monkeypatch):
    """Test OR grouping is constructed correctly."""

    mod = _resolve_mod()
    monkeypatch.setattr(mod, "parse_row_filters", lambda rf: False)

    _ = get_resource("valid-id", row_filters={"Sex": ["Male", "Female"]})

    sql = mock_env["sql"]
    assert '( "Sex"=\'Male\' OR "Sex"=\'Female\' )'.replace(" ", "") in sql.replace(" ", "")


# ---------- DUMP PATH ------------------------------------------------

def test_dump_path_when_rows_large(mock_env, monkeypatch):
    """When rows > 99999 AND no filters/col_select → dump_download()"""

    mod = _resolve_mod()
    monkeypatch.setattr(mod, "parse_row_filters", lambda rf: None)
    monkeypatch.setattr(mod, "parse_col_select", lambda c: None)

    df = get_resource("valid-id", rows=200000)

    assert mock_env["dump"] == "valid-id"
    assert isinstance(df, pd.DataFrame)


# ---------- DATASTORE SEARCH PATH ------------------------------------

def test_datastore_search_basic(mock_env, monkeypatch):
    """Test normal CKAN path when filters and SQL conditions not triggered."""

    mod = _resolve_mod()

    # Fake API JSON
    def fake_get(url, params, headers, timeout):
        assert url.endswith("/datastore_search")
        assert params["id"] == "valid-id"
        return FakeResponse({
            "result": {
                "total": 3,
                "records": [
                    {"_id": 1, "A": 10, "rank something": 5},
                    {"_id": 2, "A": 20, "rank test": 9},
                ]
            }
        })

    import requests as real_requests
    monkeypatch.setattr(mod, "requests", types.SimpleNamespace(get=fake_get, exceptions=real_requests.exceptions))

    df = get_resource("valid-id", rows=2)

    assert isinstance(df, pd.DataFrame)
    # _id and rank* dropped
    assert "_id" not in df.columns
    assert not any(col.startswith("rank ") for col in df.columns)
    assert "A" in df.columns


def test_warns_when_user_rows_more_than_total(mock_env, monkeypatch):
    mod = _resolve_mod()

    def fake_get(url, params, headers, timeout):
        return FakeResponse({
            "result": {
                "total": 10,
                "records": [{"A": 1}]
            }
        })

    import requests
    monkeypatch.setattr(mod, "requests", types.SimpleNamespace(get=fake_get, exceptions=requests.exceptions))

    with pytest.warns(UserWarning, match="only 10 rows matched"):
        get_resource("valid-id", rows=100)


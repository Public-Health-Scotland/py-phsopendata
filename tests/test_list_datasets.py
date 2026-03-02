import pytest
import requests
import pandas as pd
from phsopendata.list_datasets import list_datasets


# -----------------------------------------------------------

# -----------------------------------------------------------
def skip_if_offline():
    try:
        requests.get("https://www.opendata.nhs.scot", timeout=5)
    except Exception:
        pytest.skip("Skipping test: www.opendata.nhs.scot is offline")


# -----------------------------------------------------------
# Test: returns more than 0 datasets
# -----------------------------------------------------------
def test_list_datasets_has_rows():
    skip_if_offline()

    df = list_datasets()
    assert len(df) >= 1    


# -----------------------------------------------------------
# Test: returns data in expected format
# -----------------------------------------------------------
def test_list_datasets_expected_format():
    skip_if_offline()

    df = list_datasets()

  
    assert isinstance(df, pd.DataFrame)
    
    assert list(df.columns) == ["Name"]

    
    assert df["Name"].nunique() == len(df)
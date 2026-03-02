import pytest
import requests
import pandas as pd
from phsopendata.list_resources import list_resources


# -----------------------------------------------------------

# -----------------------------------------------------------
def skip_if_offline():
    try:
        requests.get("https://www.opendata.nhs.scot", timeout=5)
    except Exception:
        pytest.skip("Skipping test: www.opendata.nhs.scot is offline")


# -----------------------------------------------------------
# Test: returns data in expected format
# -----------------------------------------------------------
def test_list_resources_expected_format():
    skip_if_offline()

    df = list_resources("diagnostic-waiting-times")


    assert isinstance(df, pd.DataFrame)

    assert list(df.columns) == [
        "resource_id",
        "name",
        "created",
        "last_modified",
    ]

    
    assert df["resource_id"].nunique() == len(df)

 
    assert df["name"].nunique() == len(df)


# -----------------------------------------------------------
# Test: returns errors properly
# -----------------------------------------------------------
def test_list_resources_errors_properly():
    skip_if_offline()

    # Missing argument
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        list_resources()

    # bad_name => invalid format (check_dataset_name)
    with pytest.raises(
        ValueError, match=r"dataset name supplied `bad_name` is invalid"
    ):
        list_resources("bad_name")

    # incorrect-name => valid format but no match → suggest_dataset_name()
    # May return either:
    # "Can't find the dataset name incorrect-name.\ni: Did you mean X?"

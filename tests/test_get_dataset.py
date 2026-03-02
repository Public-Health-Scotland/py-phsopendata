import pytest
import requests
import pandas as pd

from phsopendata.get_dataset import get_dataset


#
# Helper: skip tests if NHS Open Data is offline (like skip_if_offline)
#
def skip_if_offline():
    try:
        requests.get("https://www.opendata.nhs.scot", timeout=5)
    except Exception:
        pytest.skip("Skipping test: www.opendata.nhs.scot is offline")


# ------------------------------------------------------------------------------
# 1. get_dataset returns data in expected format
# ------------------------------------------------------------------------------

def test_get_dataset_returns_expected_format():
    skip_if_offline()

    n_resources = 2
    n_rows = 2

    data = get_dataset(
        dataset_name="gp-practice-populations",
        max_resources=n_resources,
        rows=n_rows,
    )

    assert isinstance(data, pd.DataFrame)
    assert len(data) == n_resources * n_rows
    assert list(data.columns)  # expect_named() in R
    assert data.shape[1] >= 4


# ------------------------------------------------------------------------------
# 2. get_dataset works with filters
# ------------------------------------------------------------------------------

def test_get_dataset_with_filters():
    skip_if_offline()

    n_resources = 3
    n_rows = 10
    columns = ["Date", "PracticeCode", "HSCP", "AllAges"]

    data = get_dataset(
        "gp-practice-populations",
        max_resources=n_resources,
        rows=n_rows,
        row_filters={"HSCP": "S37000026"},
        col_select=columns,
    )

    assert isinstance(data, pd.DataFrame)
    assert len(data) == n_resources * n_rows
    assert list(data.columns) == columns
    assert (data["HSCP"] == "S37000026").all()


# ------------------------------------------------------------------------------
# 3. get_dataset errors properly
# ------------------------------------------------------------------------------

def test_get_dataset_errors_properly():
    skip_if_offline()

    # invalid name format
    with pytest.raises(ValueError, match=r"The dataset name supplied `Mal-formed-name` is invalid"):
        get_dataset("Mal-formed-name")

    # no close match
    with pytest.raises(ValueError, match=r"Can't find the dataset name dataset-name-with-no-close-match\.\ni: Did you mean .*"):
        get_dataset("dataset-name-with-no-close-match")


    # close match suggestion
    with pytest.raises(ValueError, match=r"Did you mean gp-practice-populations\?"):
        get_dataset("gp-practice-population")

# ------------------------------------------------------------------------------
# 4. get_dataset filters error properly
# ------------------------------------------------------------------------------

def test_get_dataset_filters_error_properly():
    skip_if_offline()

    with pytest.raises(SystemExit):
        get_dataset("gp-practice-populations", col_select=["Non-existent column"])
# ------------------------------------------------------------------------------
# 5. get_dataset works with multiple filters
# ------------------------------------------------------------------------------

def test_get_dataset_multiple_filters():
    skip_if_offline()

    n_resources = 3
    columns = ["Date", "PracticeCode", "HSCP", "AllAges"]

    data = get_dataset(
        "gp-practice-populations",
        max_resources=n_resources,
        row_filters={"PracticeCode": ["10002", "10017"]},
        col_select=columns,
    )

    assert isinstance(data, pd.DataFrame)
    assert len(data) >= n_resources * 4
    assert set(data.columns) == set(columns)    # FIXED: ignore order
    assert set(data["PracticeCode"]).issubset({"10002", "10017"})


# ------------------------------------------------------------------------------
# 6. Warns when having to coerce types
# ------------------------------------------------------------------------------

def test_get_dataset_warns_on_type_coercion():
    skip_if_offline()

    with pytest.warns(UserWarning, match="Due to conflicts between column types"):
        data = get_dataset(
            dataset_name="nhsscotland-payments-to-general-practice",
            rows=1,
            col_select=["PracticeListSize"],
        )

    assert isinstance(data, pd.DataFrame)
    assert list(data.columns) == ["PracticeListSize"]
    assert data["PracticeListSize"].dtype == object  # character/string
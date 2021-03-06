import pytest
from phsopendata.get_resource import get_resource
import pandas as pd
import re


def test_data_return_format():
    # Tests data is returned in the expected format
    gp_list_apr_2021 = "a794d603-95ab-4309-8c92-b48970478c14"

    # Checks type returned is a Pandas dataframe
    assert isinstance(get_resource(gp_list_apr_2021, rows=1), pd.DataFrame)
    # Checks number of columns is 15
    assert len(get_resource(gp_list_apr_2021, rows=1).columns) == 15
    # Checks number of rows is 1
    assert len(get_resource(gp_list_apr_2021, rows=1)) == 1


def test_error_argument_type():
    # Tests function calls where error is expected and handled

    # Checks wrong variable type for res_id
    with pytest.raises(ValueError) as exception_info:
        get_resource(res_id=123)
    assert exception_info.type is ValueError

    # Checks wrong format (doesn't match regex) for res_id
    with pytest.raises(ValueError) as exception_info:
        get_resource(res_id="a794d603-95ab-4309-8c92-b48970478c1")
    assert exception_info.type is ValueError
    assert re.search("The resource ID supplied \\('.+?'\\) is invalid", exception_info.value.args[0])


def test_data_complete():
    # Tests full data is returned when no rows argument is provided
    gp_list_apr_2021 = "a794d603-95ab-4309-8c92-b48970478c14"

    # Checks for total rows returned when no rows argument supplied
    assert len(get_resource(gp_list_apr_2021)) == 926


def test_data_rows():
    # Tests full data is returned when rows argument > 99999 (takes ~2min to return test result due to size of query)
    prescriptions_apr_2021 = "51b7ad3f-6d52-4165-94f4-92e322656c85"

    # Checks for total rows returned when row argument provided > 99999
    assert len(get_resource(prescriptions_apr_2021, 100000)) == 1142605

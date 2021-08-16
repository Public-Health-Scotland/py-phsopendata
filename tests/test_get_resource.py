from phsopendata.get_resource import get_resource
import pandas as pd


def test_data_return_format():
    # Tests data is returned in the expected format
    gp_list_apr_2021 = "a794d603-95ab-4309-8c92-b48970478c14"

    # Checks type returned is a Pandas dataframe
    assert isinstance(get_resource(gp_list_apr_2021, rows=1), pd.DataFrame)
    # Checks number of columns is 15
    assert len(get_resource(gp_list_apr_2021, rows=1).columns) == 15
    # Checks number of rows is 1
    assert len(get_resource(gp_list_apr_2021, rows=1)) == 1

# Get helper functions
from utils import check_res_id, ds_search_url, ds_dump_url, opendata_ua
#load packages
import re
import requests
import pandas as pd
import io

# Get Open Data resource
def get_resource(res_id, rows=None):
    """
    "Used to extract a single resource from an open dataset by resource id (res_id)"
    :param res_id: The resource ID as found on https://www.opendata.nhs.scot/ NHS Open Data platform
    :param rows: (optional) specify the max number of rows to return use this when testing code to reduce the size of
    the request it will default to all data
    :return: a Pandas dataframe with the data from the NHS Open Data platform
    """
    if not check_res_id(res_id):
        raise ValueError("The resource ID supplied ('%s') is invalid" % res_id)

    # Define the User Agent to be used for the API call
    ua = opendata_ua()

    # Return full dataset based on rows argument
    if rows is None or rows > 99999:
        if rows is not None:
            print("Queries for more than 99,999 rows of data will return the full resource.")

        try:
            response = requests.get(url=ds_dump_url(res_id), headers=ua)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        data_raw = response.text

        data = pd.read_csv(io.StringIO(data_raw))
        del data['_id']

        return data

    # Return dataset with specified number of rows
    else:
        url = "%s?id=%s&limit=%s" % (ds_search_url(), res_id, rows)

        try:
            response = requests.get(url=url, headers=ua)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        data_raw = response.json()["result"]["records"]

        data = pd.DataFrame(data_raw)
        del data['_id']

        return data

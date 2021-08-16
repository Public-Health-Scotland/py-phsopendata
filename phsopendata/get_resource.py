# Get Open Data resource

# Load required packages
import re
import requests
import pandas as pd
import io


# Open Data user agent
def opendata_ua():
    """
    "This is used internally to return a standard useragent, supplying a user agent means requests using the package
    can be tracked more easily"
    :return: a user agent string
    """
    headers = {
        "User-Agent": "https://github.com/Public-Health-Scotland/py-phsopendata"
    }

    return headers


# Check if a resource ID is valid
def check_res_id(res_id):
    """
    "Used to attempt to validate a res_id before submitting to the API"
    :param res_id: a resource ID
    :return: TRUE/FALSE indicating the validity of the res_id
    """
    res_id_regex = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    if not isinstance(res_id, str):
        return False
    if not re.search(res_id_regex, res_id):
        return False
    else:
        return True


# Create the URL for the datastore search end-point
def ds_search_url():
    """
    "Creates the URL for the datastore search end-point"
    :return: a URL
    """
    search_url = "https://www.opendata.nhs.scot/api/3/action/datastore_search"

    return search_url


# Create the URL for the datastore dump end-point
def ds_dump_url(res_id):
    """
    "Creates the URL for the datastore dump end-point"
    :param res_id: a resource ID
    :return: a URL
    """
    dump_url = "https://www.opendata.nhs.scot/datastore/dump/%s?bom=true" % res_id

    return dump_url


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

# Get Open Data resource

# Load required packages
import re

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

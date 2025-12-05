# Get helper functions

from utils import check_res_id, ds_dump_url, pkg_search_url, opendata_ua
#load packages
import re
import requests
import pandas as pd
import warnings
# Get all resources from the Open data website

def get_all_resources(package_contains = None, resource_contains = None):
    """
    " Provides an overview of all resources available from https://www.opendata.nhs.scot/, 
    with the option to limit results based on both package 
    and resource names. The returned data.frame can be used to look-up package 
    and resource ids and is useful for exploring the available data sets."
    :param package_contains: a character string containing an expression to be 
    used as search criteria against the packages 'title' field.
    :param resource_contains:  a character string containing a regular expression 
    to be matched against available resource names. If a character vector > length 1 
    is supplied, the first element is used.
    :return: a Pandas dataframe with the data from the NHS Open Data platform containing details of all available packages and 
    resources, or those containing the string specified in the package_contains and resource_contains arguments.


    """

    if package_contains is not None and not isinstance(package_contains,str):
        raise ValueError("package_contains must be None or have string length 1")
    if resource_contains is not None and not isinstance(resource_contains,str):
        raise ValueError("resource_contains must be None or have string length 1")

     # Define the User Agent to be used for the API call
    ua = opendata_ua()

    # if package contains is none

    if package_contains is None:
        url = "%s?q=*:*&rows=32000" % (pkg_search_url())
    else:
        url ="%s?q=title:%s&rows=32000" %(pkg_search_url(), package_contains)
    
    try:
        response = requests.get(url=url, headers=ua)

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    data_raw = response.json()["result"]["results"]
    #get package names
    package_names = {item["id"]: item["name"] for item in data_raw}
    #get all resources
    resources = [res for item in data_raw for res in item.get('resources', [])]
    resources_df = pd.DataFrame(resources)
    #add package names 
    resources_df['package_name'] = resources_df['package_id'].map(package_names)
    #rearrange
    data = resources_df[['name','id','package_name','package_id','url','last_modified']]
    data = data.rename(columns ={'name' : 'resource_name','id' : 'resource_id'  } )
    
    if resource_contains is not None:
        mask = data['resource_name'].str.contains(str(resource_contains), flags=re.IGNORECASE, na=False)
        data = data[mask]

    # Check if no rows match
        if data.shape[0] == 0:
            warnings.warn("No resources found for arguments provided. Returning empty DataFrame.")

  


    return data



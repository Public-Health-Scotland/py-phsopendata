# Get helper functions
from utils import opendata_ua, request_url

#Load packages
import re
import requests
import pandas as pd
import warnings
from typing import Optional

# Get all resources from the Open data website
def list_all_resources(dataset_contains: Optional[str] = None, resource_contains: Optional[str] = None) -> pd.DataFrame:
       
    """
    "Provides an overview of all resources available from https://www.opendata.nhs.scot/, 
    with the option to limit results based on both package 
    and resource names. The returned data.frame can be used to look-up package 
    and resource ids and is useful for exploring the available data sets."

    Args:
        dataset_contains (str, optional): a character string containing an expression to be used as search criteria against the dataset 'title' field. Defaults to None.
        resource_contains (str, optional): a character string containing a regular expression to be matched against available resource names. If a character vector > length 1 is supplied, the first element is used. Defaults to None.

    Returns:
        pd.DataFrame: a Pandas dataframe with the data from the NHS Open Data platform containing details of all available datasets and resources, or those containing the string specified in the dataset_contains and resource_contains arguments.

    Example:
        list_all_resources(dataset_contains = "standard-populations", resource_contains = "European")
    """    
    if dataset_contains is not None and not isinstance(dataset_contains,str):
        raise ValueError("dataset_contains must be None or have string length 1")
    if resource_contains is not None and not isinstance(resource_contains,str):
        raise ValueError("resource_contains must be None or have string length 1")

    # Define the User Agent to be used for the API call
    ua = opendata_ua()

    #query
    query = {"q":"*:*","rows":"32000"} #rows is just an aribitrary high value to avoid pagination limit
    
    try:
        response = requests.get(url=request_url("package_search"), headers=ua,params = query)

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
    data = data.rename(columns ={'name' : 'resource_name','id' : 'resource_id', 'package_name' : 'dataset_name',
    'package_id': 'dataset_id'  } )
    data['last_modified'] = pd.to_datetime(data['last_modified'],format='%Y-%m-%dT%H:%M:%S.%f').dt.floor('s') 
    
    #If package_contains is not none
    if dataset_contains is not None:
        mask = data['dataset_name'].str.contains(str(dataset_contains),flags=re.IGNORECASE,na= False)
        data = data[mask]

        if data.shape[0] == 0:
            warnings.warn("No datasets found for arguments provided. Returning empty DataFrame.")
    #If resource contains is not None
    if resource_contains is not None:
        mask = data['resource_name'].str.contains(str(resource_contains), flags=re.IGNORECASE, na=False)
        data = data[mask]

    # Check if no rows match
        if data.shape[0] == 0:
            warnings.warn("No resources found for arguments provided. Returning empty DataFrame.")

    return data



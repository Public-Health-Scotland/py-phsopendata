# Get helper functions
from utils import opendata_ua, request_url,check_dataset_name,suggest_dataset_name

#Load packages
import re
import requests
import pandas as pd
import warnings
from typing import Optional

def list_resources(dataset_name:str)-> pd.DataFrame:
    """
    "Lists all available resources for a dataset"

    Args:
        dataset_name (str): Name of the dataset as found on https://www.opendata.nhs.scot/ NHS Open Data platform.

    Returns:
        pd.DataFrame: A Pandas Data frame with the data.
    
    Example:
        list_resources("viral-respiratory-diseases-including-influenza-and-covid-19-data-in-scotland")
    """
    #throw error if name type or format is invalid
    check_dataset_name(dataset_name)
    # Define the User Agent to be used for the API call
    ua = opendata_ua()

    #define query and try API call
    query = {'id': dataset_name}
    #API call
    try:
        response = requests.get(url=request_url("package_show"), headers=ua,params = query)

    except requests.exceptions.RequestException as e:
        raise SystemExit(e) 
    
    #if it throws an error
    if "error" in response.json().keys():
        if response.json()['error']['message'] == 'Not found':
                suggest_dataset_name(dataset_name)
        
    all_ids = [resource['id'] for resource in response.json()['result']['resources']]
    all_names = [resource['name'] for resource in response.json()['result']['resources']]
    all_date_created = [resource['created'] for resource in response.json()['result']['resources']]
    all_date_created = pd.to_datetime(all_date_created, errors="coerce", utc=True).strftime("%Y-%m-%d %H:%M:%S").tolist()
    all_date_modified = [resource['last_modified'] for resource in response.json()['result']['resources']]
    all_date_modified = pd.to_datetime(all_date_modified,errors="coerce",utc=True).strftime("%Y-%m-%d %H:%M:%S").tolist()
    

    data = pd.DataFrame({'resource_id': all_ids,'name':all_names,'created':all_date_created,'last_modified':all_date_modified})

    return data





  
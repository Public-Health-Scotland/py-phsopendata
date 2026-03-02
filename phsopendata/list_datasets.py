# Get helper functions
from utils import opendata_ua, request_url

#Load packages
import requests
import pandas as pd


def list_datasets()-> pd.DataFrame:
    """
    "Lists all available datasets"

    Returns:
        pd.DataFrame: A Pandas dataframe with names of all the datasets hosted on the phs open data platform.
    
    Example:
        head(list_datasets())
    """


    content = requests.get(url = request_url("package_list"),params = " ")
    data = pd.DataFrame(content.json()["result"]).rename(columns={0:"Name"})

    return data

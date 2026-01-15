# Get helper functions
from get_resource import get_resource
from utils import opendata_ua, check_dataset_name,request_url, suggest_dataset_name

#Load packages

import requests
import pandas as pd
import warnings
from typing import Optional, List, Any, Mapping, Sequence


def get_dataset(dataset_name: str, max_resources: Optional[int] = None, rows: Optional[int] = None,
row_filters: Optional[Mapping[str, Any]] = None, col_select: Optional[Sequence[str]] = None, 
include_context: Optional[bool] = False) -> pd.DataFrame:
    """
    "Downloads a single resource from the NHS Open Data platform by resource ID, with optional filtering and column selection."

    Args:
        dataset_name (str): Name of the dataset as found on https://www.opendata.nhs.scot/ NHS Open Data platform.
        max_resources (int, optional): The maximum number of resources to return (Integer). If not set, all resources are returned. Defaults to None.
        rows (Optional[int], optional): Maximum number of rows to return. Defaults to None.
        row_filters (Optional[Mapping[str, Any]], optional): A dictionary of column/field filters to keep, e.g.:`{"Date": 20220216, "Sex": "Female"}`. Each key is the column name and the value is the desired value.
        col_select (Optional[Sequence[str]], optional): A list/tuple of column/field names to include, e.g.:`["Date", "Sex"]`. If None, all columns are returned.
        include_context (bool, optional): If `TRUE`, additional information about the resource will be added as columns to the data, including the resource ID, the resource name, the creation date, and the last modified/updated date. Defaults to False.

    Returns:
        pd.DataFrame: A Pandas Data frame with the data.
    
    Example:
        get_dataset("gp-practice-populations", max_resources = 2, rows = 10)
    """
    #throw error if name type or format is invalid
    check_dataset_name(dataset_name)
    # Define the User Agent to be used for the API call
    ua = opendata_ua()

    #define query
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
    
    #define list of resource IDs to get
    all_ids = [res["id"] for res in response.json()["result"]["resources"]]

    n_res = len(all_ids)
    cap = n_res if max_resources is None else min(n_res, max_resources)
    
 
    selection_ids = all_ids[:cap] 

    # get all resources
    
    all_data: List[pd.DataFrame] = [
        get_resource(
            res_id=selection_id,
            rows=rows,
            row_filters=row_filters,
            col_select=col_select,
        )
        for selection_id in selection_ids
    ]

    #Resolve class/type issues across DataFrames
    types = [{col: str(df[col].dtype) for col in df.columns} for df in all_data]
    
    to_coerce = set()
    for i in range(len(types) - 1):
        this_types = types[i]
        next_types = types[i + 1]
        common_cols = [c for c in this_types if c in next_types]
        for c in common_cols:
            if this_types[c] != next_types[c]:
                to_coerce.add(c)
    
    if to_coerce:
            warnings.warn(
                "Due to conflicts between column types across resources, "
                f"the following column(s) have been coerced to type string: {sorted(to_coerce)}"
            )
            coerced_data = []
            
            for df in all_data:
                # Only coerce columns that exist in this df
                cols_to_cast = {c: df[c].astype(str) for c in df.columns if c in to_coerce}
                if cols_to_cast:
                    df = df.assign(**cols_to_cast)
                coerced_data.append(df)
            all_data = coerced_data




    if include_context:
        context = []
        for selection_id, df in zip(selection_ids, all_data):
            try:
                ctx_resp = requests.get(
                    url=request_url("resource_show"),
                    params={"id": selection_id},
                    headers=ua,
                    timeout=60,
                )
                ctx_resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            ctx = ctx_resp.json().get("result", {})

   
            df = df.assign(
                resource_id=ctx.get("id"),
                resource_name=ctx.get("name"),
                created_date=pd.to_datetime(ctx.get("created"), utc=True).strftime("%Y-%m-%d %H:%M:%S"),
                last_modified= pd.to_datetime(ctx.get("last_modified"),errors="coerce",utc=True).strftime("%Y-%m-%d %H:%M:%S")
            )

            context.append(df)
        all_data = context

    combined = pd.concat(all_data, ignore_index=True)

    return combined




   





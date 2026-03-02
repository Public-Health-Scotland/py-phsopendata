# Get helper functions
from phsopendata.utils import check_res_id, get_resource_sql, request_url, dump_download, opendata_ua, parse_col_select,parse_row_filters
#load packages
import requests
import warnings
import pandas as pd
from typing import Optional, Any, Mapping, Dict, Sequence
import json

# Get Open Data resource
def get_resource(res_id:str, rows:Optional[int]=None, row_filters: Optional[Mapping[str, Any]] = None, col_select: Optional[Sequence[str]] = None,include_context: Optional[bool] = False) -> pd.DataFrame:
    """
    "Used to extract a single resource from an open dataset by resource id (res_id)"


    Args:
        res_id (str):  The resource ID as found on https://www.opendata.nhs.scot/ NHS Open Data platform
        rows (Optional[int], optional): specify the max number of rows to return use this when testing code to reduce the size of the request it will default to all data. Defaults to None.
        row_filters (Optional[Mapping[str, Any]], optional): A dictionary of column/field filters to keep, e.g.:`{"Date": 20220216, "Sex": "Female"}`. Each key is the column name and the value is the desired value. Defaults to None.
        col_select (Optional[Sequence[str]], optional): A list/tuple of column/field names to include, e.g.:`["Date", "Sex"]`. If None, all columns are returned. Defaults to None.
        include_context (Optional[bool], optional):  If `TRUE`, additional information about the resource will be added as columns to the data, including the resource ID, the resource name, the creation date, and the last modified/updated date. Defaults to False.

 

    Returns:
        pd.DataFrame: a Pandas dataframe with the data from the NHS Open Data platform.
    
    Example:
        get_resource(res_id="bcc860a4-49f4-4232-a76b-f559cf6eb885",row_filters={"Hospital" : "D102H"},col_select=["TotalCancelled", "TotalOperations", "Hospital", "Month"])
    """    
  
    if not check_res_id(res_id):
        raise ValueError("The resource ID supplied ('%s') is invalid" % res_id)

    parsed_col_select = parse_col_select(col_select)
    parsed_row_filters = parse_row_filters(row_filters)


    # Define the User Agent to be used for the API call
    ua = opendata_ua()

    # If parse_row_filters signals "use SQL" (multi-value or Sex='All')
    if isinstance(parsed_row_filters, bool) and parsed_row_filters is False:
        if row_filters is not None:
            # Build SELECT list: "*" or quoted column names
            if col_select is None or len(col_select) == 0:
                col_select_sql = "*"
            else:
                # Quote each column name with double quotes, join with commas
                col_select_sql = ",".join(f'"{c}"' for c in col_select)

            # Build WHERE: each key can have one or multiple values
            clauses = []
            for col, val in row_filters.items():
                # Normalize to a list of values
                vals = (
                    list(val)
                    if isinstance(val, (list, tuple, set))
                    else [val]
                )
                # Escape single quotes inside values
                def _esc(v):
                    s = str(v)
                    return s.replace("'", "''")

                or_group = " OR ".join([f'"{col}"=\'{_esc(v)}\'' for v in vals])
                clauses.append(f"({or_group})")

            where_sql = " AND ".join(clauses) if clauses else "TRUE"

            # LIMIT part
            limit_sql = "" if rows is None else f" LIMIT {int(rows)}"

            # Final SQL (quote table name with double quotes)
            sql = f'SELECT {col_select_sql} FROM "{res_id}" WHERE {where_sql}{limit_sql}'
            data = get_resource_sql(sql)
        else:
            # No filters supplied but parse_row_filters returned False? Fallback to dump/search.
            data = dump_download(res_id)
    else:
        # Build query for datastore_search
        query: Dict[str, Any] = {
            "id": res_id,
            "limit": rows,
            "fields": parsed_col_select,
        }

        # Use "dump" if rows is None or > CKAN max (99999) AND no filters AND no col selection
        # (This approximates the R use_dump_check behaviour.)
        use_dump = (
            (rows is None or (isinstance(rows, int) and rows > 99999))
            and parsed_row_filters is None
            and parsed_col_select is None
        )

        if use_dump:
            data = dump_download(res_id)
        else:
            # If no specific row limit set, default to CKAN max
            if query.get("limit") is None:
                query["limit"] = 99999
            
            if isinstance(parsed_row_filters, str):
                query["filters"] = parsed_row_filters
            elif row_filters is not None:
                query["filters"] = json.dumps(row_filters)

            # Remove None values from query
            query = {k: v for k, v in query.items() if v is not None}

            # Fetch data
            try:
                response = requests.get(
                    url=request_url("datastore_search"),
                    params=query,
                    headers=ua,
                    timeout=60,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise SystemExit(e)

            res_content = response.json()
            result = res_content.get("result", {})
            total_rows = result.get("total", None)
            records = result.get("records", [])

            # Warnings similar to R implementation
            limit_val = query.get("limit")
            if total_rows is not None:
                if rows is None and isinstance(limit_val, int) and limit_val < total_rows:
                    warnings.warn(
                        f"Returning the first {limit_val} results (rows) of your query. "
                        f"{total_rows} rows match your query in total. "
                        "To get ALL matching rows you will need to download the whole "
                        "resource and apply filters/selections locally.",
                        stacklevel=2,
                    )
                if rows is not None and isinstance(limit_val, int) and limit_val > total_rows:
                    warnings.warn(
                        f"You set rows to {limit_val} but only {total_rows} rows matched your query.",
                        stacklevel=2,
                    )

            data = pd.DataFrame(records)

            # Drop columns starting with "rank " and '_id'
            drop_cols = [c for c in data.columns if c.startswith("rank ")]
            if "_id" in data.columns:
                drop_cols.append("_id")
            data = data.drop(columns=drop_cols, errors="ignore")

    # Include context columns if requested
    if include_context:
        try:
            ctx_resp = requests.get(
                url=request_url("resource_show"),
                params={"id": res_id},
                headers=ua,
                timeout=60,
            )
            ctx_resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        ctx = ctx_resp.json().get("result", {})
        data = data.assign(
            resource_id=ctx.get("id"),
            resource_name=ctx.get("name"),
            created_date=pd.to_datetime(ctx.get("created"), utc=True).strftime("%Y-%m-%d %H:%M:%S"),
            last_modified=pd.to_datetime(ctx.get("last_modified"), utc=True).strftime("%Y-%m-%d %H:%M:%S")
        )

    return data

   
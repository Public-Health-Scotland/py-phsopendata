# Load required packages
import re
import requests
import pandas as pd
import io
from rapidfuzz import process, fuzz
from typing import Iterable, Optional, Union, List, Any, Mapping, Tuple, Dict, Sequence
import json

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

# Creates a URL for a GET request to opendata.nhs.scot
def request_url(action:str)-> str:  
    """
    "Produces a URL for a GET request to opendata.nhs.scot"

    Args:
        action (str): The API endpoint you want to use, e.g., "package_show" / "datastore_search".
    Returns:
        str: a URL as a character string

    """    
    #check whether action is valid
    valid_actions = ['datastore_search',"datastore_search_sql","package_show","package_list",
    "resource_show","package_search"]
    if action not in valid_actions:
        raise ValueError(
            ("API call failed.\n"
             f"x: {action} is an invalid argument"
            ))
    
    base_url =  "https://www.opendata.nhs.scot"

    url = base_url + "/api/3/action/"+ action
    
    return url

# dump url
def ds_dump_url(res_id):
    """
    "Creates the URL for the datastore dump end-point"
    :param res_id: a resource ID
    :return: a URL
    """
    dump_url = "https://www.opendata.nhs.scot/datastore/dump/%s?bom=true" % res_id

    return dump_url

# dump (full resource download)
def dump_download(res_id_: str) -> pd.DataFrame:
        ua = opendata_ua()
        try:
            response = requests.get(url=ds_dump_url(res_id_), headers=ua, timeout=120)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        data_raw = response.text
        df = pd.read_csv(io.StringIO(data_raw))
        # Drop _id if present
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        return df



# Check dataset name -  throws an error if a dataset name is invalid
def check_dataset_name(dataset_name:str = None):
    # Starts and ends in a lowercase letter or number
    # Has only lowercase alphanum or hyphens inbetween
  dataset_name_regex = r"^[a-z0-9][a-z0-9\\-]+?[a-z0-9]$"
  if not isinstance(dataset_name,str):
    raise TypeError(
        (f"The dataset name supplied `{dataset_name}` is invalid.\n"
         f"x: dataset_name must be of type character (str).\n"
         f"i: You supplied a `{type(dataset_name).__name__}` value.") )
    
  if not re.search(dataset_name_regex,dataset_name):
        raise ValueError(
            (
                f"The dataset name supplied `{dataset_name}` is invalid.\n"
                "x: dataset_name must be in dash-case "
                "(e.g., lowercase-words-separated-by-dashes).\n"
                "i: You can find dataset names in the URL of a dataset's page on www.opendata.nhs.scot"
            ))

# Suggest dataset name
def suggest_dataset_name(dataset_name:str)-> str:
    content = requests.get(url=request_url("package_list"))
    dataset_names = content.json()["result"]

    #calculate string distances
    stringdistance = process.extractOne(dataset_name,dataset_names,scorer=fuzz.WRatio)

    if stringdistance[1] > 50:
        raise ValueError(
            f"Can't find the dataset name {dataset_name}.\n"
            f"i: Did you mean {stringdistance[0]}?"
        )
    else:
        raise ValueError(
            f"Can't find the dataset name {dataset_name} or a close match.\n"
            "i: You can find dataset names in the URL of a dataset's page on www.opendata.nhs.scot."
        )

#parse_col_select function
def parse_col_select(col_select: Optional[Union[str, Iterable[Any]]]) -> str:
    """
    "Create fields query for datastore_search_sql."

    Args:
        col_select (Optional[Union[str, Iterable[Any]]]): The desired columns/fields. May be:
        - None -> returns None
        - A single string -> returned as-is
        - An iterable (list/tuple/etc.) of strings (possibly nested) -> flattened, deduped


    Returns:
        Optional[str]: A comma-separated string of unique column names, or None if input is None.
    """    
    
    if col_select is None:
        return None

    # Normalize to a flat list of items
    def _flatten(items):
        for x in items:
            if isinstance(x, (list, tuple)):
                yield from _flatten(x)
            else:
                yield x

    # If a single string is passed, return it (after basic validation)
    if isinstance(col_select, str):
        value = col_select.strip()
        if not value:
            raise TypeError("col_select must not be an empty string.")
        return value

    # Otherwise, treat as an iterable (excluding strings which are iterable-bytes)
    if isinstance(col_select, (list, tuple)):
        flat: List[Any] = list(_flatten(col_select))
    else:
        # Not a string, list, or tuple -> invalid (e.g., int, dict, set)
        raise TypeError(
            f"col_select must be a string or a list/tuple of strings, not {type(col_select).__name__}."
        )

    # Drop duplicates while preserving order
    seen = set()
    unique_items: List[str] = []
    for item in flat:
        if isinstance(item, str):
            key = item
        else:
            raise TypeError(
                f"col_select must contain only strings; found {type(item).__name__}."
            )
        if key not in seen:
            seen.add(key)
            unique_items.append(key)

    if not unique_items:
        raise TypeError("col_select must contain at least one non-empty string.")

    # Join into a comma-separated string
    return ",".join(unique_items)


#parse_row_select function


def parse_row_filters(
    row_filters: Optional[Union[Mapping[str, Any], Iterable[Tuple[str, Any]]]]
) -> Optional[Union[str, bool]]:
    """
    Create JSON 'dict' from named filters for use in a GET request.

    Mirrors R's parse_row_filters():
      - None -> None
      - Validate type: must be a mapping/dict, or iterable of (key, value) pairs.
      - Keys must be non-empty strings; duplicates are rejected.
      - If 'Sex' filter equals 'All' (or includes 'All') -> return False (use SQL).
      - If any field has multiple values (length > 1) -> return False (use SQL).
      - Otherwise, return a JSON object string with all values stringified.

    Returns
    -------
    Optional[Union[str, bool]]
        None (no filters), False (force SQL), or JSON string.

    Raises
    ------
    TypeError
        If the input is not a mapping or iterable of (key, value) pairs, or keys invalid.
    ValueError
        If duplicate keys are detected.
    """
    # 1) No filters
    if row_filters is None:
        return None

    # 2) Normalize input to a list of (key, value) pairs
    items: List[Tuple[str, Any]] = []
    if isinstance(row_filters, Mapping):
        items = list(row_filters.items())
    elif isinstance(row_filters, (list, tuple)):
        # Expect list/tuple of (key, value) pairs
        try:
            items = [(k, v) for (k, v) in row_filters]  # will raise if wrong shape
        except Exception:
            raise TypeError(
                "row_filters must be a dict or an iterable of (key, value) pairs."
            )
    else:
        # You could optionally support pandas Series here:
        # if isinstance(row_filters, pd.Series): items = list(row_filters.items())
        raise TypeError(
            f"row_filters must be a dict or an iterable of (key, value) pairs, not {type(row_filters).__name__}."
        )

    # 3) Validate keys and detect duplicates
    seen = set()
    for k, _ in items:
        if not isinstance(k, str) or not k.strip():
            raise TypeError("All filter keys must be non-empty strings.")
        if k in seen:
            raise ValueError(
                f"Duplicate filter detected for field '{k}'. Only one filter per field is supported."
            )
        seen.add(k)

    # 4) Special case: Sex == "All" (or includes "All") -> force SQL path (return False)
    for k, v in items:
        if k == "Sex":
            if isinstance(v, (list, tuple, set)):
                if any(str(x) == "All" for x in v):
                    return False
            else:
                if str(v) == "All":
                    return False

    # 5) If any field has multiple values (length > 1), return False (use SQL)
    for _, v in items:
        if isinstance(v, (list, tuple, set)):
            # If the container has >1 values, we signal SQL
            if len(v) > 1:
                return False
            # If it has exactly one, treat it as a scalar
            if len(v) == 1:
                v_scalar = next(iter(v))
                # Replace in items (maintain order)
                # (build a new list to avoid mutating while iterating)
                pass

    # Rebuild items with singletons unwrapped
    normalized_items: List[Tuple[str, Any]] = []
    for k, v in items:
        if isinstance(v, (list, tuple, set)):
            if len(v) == 0:
                raise TypeError(f"Filter '{k}' cannot be an empty collection.")
            if len(v) == 1:
                v = next(iter(v))
            else:
                # Already handled above, but keep defensive
                return False
        normalized_items.append((k, v))

    # 6) Produce a JSON object string with *stringified* values (parity with R which quotes values)
    payload: Dict[str, str] = {k: str(v) for k, v in normalized_items}
    return json.dumps(payload, ensure_ascii=False)

# SQL fetch via datastore_search_sql
def get_resource_sql(sql: str) -> pd.DataFrame:
    ua = opendata_ua()

    try:
            resp = requests.get(
                url=request_url("datastore_search_sql"),
                params={"sql": sql},
                headers=ua,
                timeout=60,
            )
            resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    result = resp.json().get("result", {})
    records = result.get("records", [])
    df = pd.DataFrame(records)
        # Drop rank* and _id columns
    drop_cols = [c for c in df.columns if c.startswith("rank ")] + (
    ["_id"] if "_id" in df.columns else []
    )
    df = df.drop(columns=drop_cols, errors="ignore")
    return df


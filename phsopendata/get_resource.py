# Get Open Data resource


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

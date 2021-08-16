# Python phsopendata (py-phsopendata)

*In early development*

<!-- badges: start -->
[![Build Status](https://www.travis-ci.com/Public-Health-Scotland/py-phsopendata.svg?branch=main)](https://www.travis-ci.com/Public-Health-Scotland/py-phsopendata)
<!-- badges: end -->

The Python `phsopendata` package contains functions to interact with open data from the
[Scottish Health and Social Care Open Data
platform](https://www.opendata.nhs.scot/) via the CKAN API.

-   `get-resource` extracts a single resource from an open dataset by
    resource id

For extracting metadata and search functionality, we recommend using the
[ckanr package](https://docs.ropensci.org/ckanr/).


Installation
------------

When the first phase of development is complete, this package will be hosted on PyPI for simplified installation. To use `phsopendata` just now, install directly from GitHub with:

    pip install git+https://github.com/Public-Health-Scotland/py-phsopendata.git


Examples
--------

### get\_resource()

To extract a specific resource, you will need its unique identifier -
resource id. This can be found in the dataset metadata by visiting the
website, or extracted using `ckanr.package_show`.

    import phsopendata

    # by default the full resource is returned
    get_resource(res_id="a794d603-95ab-4309-8c92-b48970478c14")

    # but you can set the number of rows to return
    get_resource(res_id="a794d603-95ab-4309-8c92-b48970478c14", rows=10)


Contributing to phsopendata
---------------------------

At present, this package is maintained by [Russell McCreath](https://github.com/rmccreath). This is directly translated from the [R phsopendata package](https://github.com/Public-Health-Scotland/phsopendata).

If you have requests or suggestions for additional functionality, please
contact the package maintainer and/or the [PHS Open Data
team](phs.opendata@phs.scot).

If you would like to share examples of how you work with open data, you
can also do so in the [Open Data
repository](https://github.com/Public-Health-Scotland/Open-Data), where
example scripts and resources are collated.

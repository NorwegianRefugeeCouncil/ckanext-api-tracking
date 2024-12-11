[![Tests](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/workflows/Tests/badge.svg)](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/actions)

This repository contains a CKAN open-source extension that can be added to any CKAN 2.10+ instance. It was developed by Norwegian Refugee Council (NRC) and Open Knowledge Foundation (OKFN).

# CKAN API tracking extension

This extension allows CKAN portals to monitor the use of API tokens by users or service accounts.

## Use-cases

NRC uses this extension in the following way:

 - Track API usage by dataset and organization.
 - Track API usage by users.
 - Track API usage by API token.

## How it works

This extension adds a new middleware to the CKAN application that intercept all API requests and log them into the CKAN database. A new database table was created to store this information. This table is similar to the current CKAN `tracking_raw` table (in use at the `TrackingMiddleware`). Considering the similarities with the CKAN core feature, a possible future for this extension is to capture all calls and unify usage tracking.

This extension also includes a series of dashboards with a summary of the available data. These dashboards are based on the CKAN core `StatsPlugin` plugin. This extension eventually will attempt to replace the current `stats` plugin.

All data from this extension is only accessible by sysadmins.

### Sample screenshots

![Token usage by name](/DOCS/imgs/token-usage-by-name.png)
![Token usage by dataset](/DOCS/imgs/token-usage-by-data-file.png)
![Latest Token usage](/DOCS/imgs/latest-token-usage.png)

### API endpoints

 - all_token_usage: `/api/action/all_token_usage[?limit=10]` It returns all API requests with a user token. Sort by date.
 - most_accessed_dataset_with_token: `/api/action/most_accessed_dataset_with_token[?limit=10]` It returns the most accessed datasets with a user token. Sort by most requested dataset.
 - most_accessed_token: `/api/action/most_accessed_token[?limit=10]` It returns the most accessed user token. Sort by most used token.

![Api calls](/DOCS/imgs/api-calls.png)

### CSV endpoints

A more _human-readable_ way to access the same API data through CSV files. The following endpoints are available:

 - `/tracking-csv/most-accessed-dataset-with-token.csv`
 - `/tracking-csv/most-accessed-token.csv`
 - `/tracking-csv/all-token-usage.csv`

### Questions / issues

Please feel free to [start an issue](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/issues) or send direct questions to Andrés Vázquez (@avdata99) or Nadine Levin (@nadineisabel). Thanks for reading!


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.10            | Yes           |
| 2.11            | Not tested    |


## Installation

To install ckanext-api-tracking:

Install the package:

    pip install -e "git+https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking.git@main#egg=ckanext-api-tracking"
    pip install -r https://raw.githubusercontent.com/NorwegianRefugeeCouncil/ckanext-api-tracking/main/requirements.txt

or clone the source and install it on the virtualenv

    git clone https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking.git
    cd ckanext-api-tracking
    pip install -e .
	pip install -r requirements.txt

3. Add `tracking` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN.

## Config settings

#### track_anon

By default, this plugin does not track actions if there is no Authorization header or API Token present in the request. To enable tracking of anonymous actions (no user logged in), enable the following config option:

```
ckanext.api_tracking.track_anon = True
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

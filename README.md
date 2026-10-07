[![Tests CKAN 2.12](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/workflows/Tests%20CKAN%202.12/badge.svg)](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/actions)
[![Tests CKAN 2.11](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/workflows/Tests%20CKAN%202.11/badge.svg)](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/actions)
This repository contains a CKAN open-source extension that can be added to any CKAN 2.11+ instance. It was developed by Norwegian Refugee Council (NRC) and Open Knowledge Foundation (OKFN).  

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

See [tracking_type.md](/DOCS/imgs/tracking_type.md) for more information on the tracking fields.  

### Sample screenshots

![Token usage by name](/DOCS/imgs/token-usage-by-name.png)
![Token usage by dataset](/DOCS/imgs/token-usage-by-data-file.png)
![Latest Token usage](/DOCS/imgs/latest-token-usage.png)

### API endpoints

 - all_token_usage: `/api/action/all_token_usage[?limit=10]` It returns all API requests with a user token. Sort by date.
 - most_accessed_dataset_with_token: `/api/action/most_accessed_dataset_with_token[?limit=10]` It returns the most accessed datasets with a user token. Sort by most requested dataset.
 - most_accessed_token: `/api/action/most_accessed_token[?limit=10]` It returns the most accessed user token. Sort by most used token.
 - users_active_metrics: `/api/action/users_active_metrics[?limit=10]` It returns the most active users. Sort by most active user.
 - usage_by_user: `/api/action/usage_by_user[?days=30&limit=100]` It returns usage per user in the last `days` days (API token requests, tokens used, logins, last seen). Sort by most active user.

![Api calls](/DOCS/imgs/api-calls.png)

### CSV endpoints

A more _human-readable_ way to access the same API data through CSV files. The following endpoints are available:

 - `/tracking-csv/most-accessed-dataset-with-token.csv`
 - `/tracking-csv/most-accessed-token.csv`
 - `/tracking-csv/all-token-usage.csv`
 - `/tracking-csv/users-active-metrics.csv`
 - `/tracking-csv/usage-by-user.csv[?days=7|30|90|365]`

### Questions / issues

Please feel free to [start an issue](https://github.com/NorwegianRefugeeCouncil/ckanext-api-tracking/issues) or send direct questions to Andrés Vázquez (@avdata99) or Nadine Levin (@nadineisabel). Thanks for reading!


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.10            | Until 0.5.3   |
| 2.11            | Yes           |
| 2.12            | Yes           |


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

Add `api_tracking` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).
It's also required to add the core extenstion `tracking` to the `ckan.plugins` setting.


Restart CKAN.

## Config settings

Login and logout events are not tracked by default. To track them:

```
ckanext.api_tracking.track_login = true  # default is false
ckanext.api_tracking.track_logout = true # default is false
```

Web visits are tracked by default (this extension exists to track usage).
To disable them:

```
ckanext.api_tracking.track_ui_users = false      # default is true
ckanext.api_tracking.track_ui_anonymous = false  # default is true
```

`track_ui_users` and `track_ui_anonymous` store the web pages (datasets, resources,
downloads, organizations and their lists) visited by logged in and anonymous users.
This happens on the server: no JavaScript and no `POST /_tracking` like CKAN core tracking.
Requests made with an API token are always tracked.

Each web visit gets a `visitor_key` to count unique visitors: a hash of IP + browser,
salted with the app secret and the date. The IP is never stored and keys change every day.

Bots are not tracked for anonymous visits. The default list of ignored user agents
can be replaced with a regular expression (case insensitive):

```
ckanext.api_tracking.ignore_user_agents = bot|crawl|spider|curl
```


### Internal service downloads

To distinguish automated resource downloads from web downloads, list service
API token names (space-separated; empty by default):

```ini
ckanext.api_tracking.internal_token_names = datapusher_multi
```

Downloads authenticated with these tokens are stored as `internal.download`.
They remain in token usage metrics, and their classification is visible in the
dashboard, CSV and API. Reserve these names for service tokens: the name is an
operational convention, not proof that a request originated from XLoader.
Existing events are not reclassified. XLoader POST callbacks (`xloader_hook`)
are deliberately excluded from usage tracking.

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

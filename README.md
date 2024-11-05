[![Tests](https://github.com/NorwegianRefugeeCouncil/ckanext-tracking/workflows/Tests/badge.svg)](https://github.com/NorwegianRefugeeCouncil/ckanext-tracking/actions)

# CKAN API tracking extension

This repository contains a CKAN open-source extension that can be added to any CKAN instance. It was developed by Norwegian Refugee Council (NRC) and Open Knowledge Foundation (OKFN).  
It is intended to help other CKAN portals be able to **monitor API usage** for UI usage metrics and data privacy concerns.

## Use-Case

NRC uses this extension in the following way:

 - Track API usage by dataset and organization.
 - Track API usage by users.
 - Track API usage by API token.

## How it works?

This extension adds a new middleware to the CKAN application that intercept all API requests and log them into a database.  
A new database table was created to store this information. This table is similar to the current CKAN `tracking` extension table.  
Considering the similarities with the `tracking` CKAN core extension, a possible future for extension is to capture all calls and unify usage tracking.  

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

A more _human-readable_ way to access the same API data through CSV files.  
The following endpoints are available:

 - `/tracking-csv/most-accessed-dataset-with-token.csv`
 - `/tracking-csv/most-accessed-token.csv`
 - `/tracking-csv/all-token-usage.csv`

### Questions / issues

Please feel free to [start an issue](https://github.com/NorwegianRefugeeCouncil/ckanext-tracking/issues) or send direct questions to Andrés Vázquez (@avdata99) or Nadine Levin (@nadineisabel).  


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.10            | Yes           |
| 2.11            | not tested    |


## Installation

To install ckanext-tracking:

Install the package:

    pip install -e "git+https://github.com/NorwegianRefugeeCouncil/ckanext-tracking.git@main#egg=ckanext-tracking"
    pip install -r https://raw.githubusercontent.com/NorwegianRefugeeCouncil/ckanext-tracking/main/requirements.txt

or clone the source and install it on the virtualenv

    git clone https://github.com/NorwegianRefugeeCouncil/ckanext-tracking.git
    cd ckanext-tracking
    pip install -e .
	pip install -r requirements.txt

3. Add `tracking` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN.

## Config settings

None at present

## Data access

URL to get CSV file with most accessed datasets with token: /tracking-csv/most-accessed-dataset-with-token.csv  
API call: /api/action/most_accessed_dataset_with_token  

In progress

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

"""
Relevant queries to tracking data
"""
import csv


def rows_as_dicts(query):
    """
    Run a SQLAlchemy query and return the rows as plain dicts.
    SQLAlchemy 2 (CKAN 2.12) Row objects no longer accept string keys,
    dicts keep row['column'] working (also on SQLAlchemy 1.4 / CKAN 2.11).
    """
    return [dict(row._mapping) for row in query]


def download_query_results_as_csv(query_results, filename):
    """
    Download query results as CSV
    """
    f = open(filename, 'w')
    writer = csv.writer(f)
    # include headers
    writer.writerow(query_results[0].keys())
    writer.writerows(query_results)
    f.close()

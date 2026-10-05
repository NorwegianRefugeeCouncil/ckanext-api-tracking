"""
Relevant queries to tracking data
"""


def rows_as_dicts(query):
    """
    Run a SQLAlchemy query and return the rows as plain dicts.
    SQLAlchemy 2 (CKAN 2.12) Row objects no longer accept string keys,
    dicts keep row['column'] working (also on SQLAlchemy 1.4 / CKAN 2.11).
    """
    return [dict(row._mapping) for row in query]

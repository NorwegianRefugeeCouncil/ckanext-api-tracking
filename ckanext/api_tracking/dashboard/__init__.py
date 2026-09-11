import logging
from pathlib import Path
from sqlalchemy.sql.expression import text
from ckan import model


log = logging.getLogger(__name__)


def query_results(sql_file, params={}):
    """ Query a sql file in the sql directory """
    here = Path(__file__).parent
    engine = model.meta.engine
    sql_file = here / 'sql' / sql_file
    f = open(sql_file, 'r')
    sql = f.read()
    f.close()
    log.debug(f'Executing SQL: {sql} :: {params}')
    text_sql = text(sql)
    # SQLAlchemy 2 (CKAN 2.12): Engine.execute() is gone and Row objects no
    # longer accept string keys, so run on a connection and return plain dicts
    # (row['column'] keeps working for every caller). Also fine on SQLAlchemy 1.4.
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(text_sql, params)]

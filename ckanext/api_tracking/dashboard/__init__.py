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
    return engine.execute(text_sql, **params).fetchall()

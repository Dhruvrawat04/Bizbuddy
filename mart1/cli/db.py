"""Re-export database helpers from the main mart1 db module."""

import importlib.util
from pathlib import Path

_parent_db = Path(__file__).resolve().parent.parent / "db.py"
_spec = importlib.util.spec_from_file_location("mart1_db", _parent_db)
_mart1_db = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mart1_db)

CONNECTION_STRING = _mart1_db.CONNECTION_STRING
DATABASE_URL = _mart1_db.DATABASE_URL
DB_HOST = _mart1_db.DB_HOST
DB_NAME = _mart1_db.DB_NAME
DB_USER = _mart1_db.DB_USER
DB_PASS = _mart1_db.DB_PASS
DB_PORT = _mart1_db.DB_PORT
engine = _mart1_db.engine
get_connection = _mart1_db.get_connection
get_connection_string = _mart1_db.get_connection_string
get_engine = _mart1_db.get_engine

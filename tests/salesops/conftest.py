import pytest

@pytest.fixture(scope="session",autouse=True)
def salesops_database(tmp_path_factory):
    path=tmp_path_factory.mktemp("salesops")/"test.db"
    import core.database as db
    import database.import_data as importer
    db.DB_PATH=path;importer.DB_PATH=path
    importer.initialize_database(overwrite=True,profile="mvp",seed=42)
    from legacy_crm.app import ensure_table
    ensure_table()
    return path

@pytest.fixture
def users():
    from core.auth import authenticate
    return {name:authenticate(name,"salesops-demo") for name in ["admin","manager","builder"]}


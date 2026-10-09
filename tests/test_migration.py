import importlib.util
from pathlib import Path
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine,inspect
from app.database import Base

def test_migrations_match_models_and_revert():
    modules=[]
    for path in sorted((Path(__file__).resolve().parent.parent / "migrations/versions").glob("*.py")):
        spec=importlib.util.spec_from_file_location(path.stem,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);modules.append(module)
    engine=create_engine("sqlite://")
    with engine.begin() as c:
        context=MigrationContext.configure(c)
        with Operations.context(context):
            for module in modules:module.upgrade()
            assert compare_metadata(context,Base.metadata)==[]
            for module in reversed(modules):module.downgrade()
            assert inspect(c).get_table_names()==[]

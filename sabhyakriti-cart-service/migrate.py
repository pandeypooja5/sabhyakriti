"""Run alembic migrations without path shadowing issues."""
import sys, os
# Remove '' from sys.path so local alembic/ dir doesn't shadow the installed package
sys.path = [p for p in sys.path if p not in ('', os.getcwd())]
from alembic.config import Config
from alembic import command
cfg = Config("alembic.ini")
command.upgrade(cfg, "head")
print("Migration complete.")

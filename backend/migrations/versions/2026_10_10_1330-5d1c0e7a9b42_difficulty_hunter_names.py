"""difficulty hunter names: normal/hard/hunter -> awakened/national/monarch (+ elite)

Revision ID: 5d1c0e7a9b42
Revises: a9fe2558b808
Create Date: 2026-10-10 13:30:00

"""
from typing import Sequence, Union

from alembic import op


revision: str = '5d1c0e7a9b42'
down_revision: Union[str, Sequence[str], None] = 'a9fe2558b808'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Column is a plain VARCHAR (native_enum=False, no CHECK), so only the stored values change.
RENAMES = {'normal': 'awakened', 'hard': 'national', 'hunter': 'monarch'}


def upgrade() -> None:
    for old, new in RENAMES.items():
        op.execute(f"UPDATE profiles SET difficulty = '{new}' WHERE difficulty = '{old}'")


def downgrade() -> None:
    op.execute("UPDATE profiles SET difficulty = 'awakened' WHERE difficulty = 'elite'")
    for old, new in RENAMES.items():
        op.execute(f"UPDATE profiles SET difficulty = '{old}' WHERE difficulty = '{new}'")

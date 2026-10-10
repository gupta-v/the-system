"""day kinds per weekday: the day type moves from the Routine to the weekday

Revision ID: c4a8e2f1b7d3
Revises: 7b3e9c1d2f54
Create Date: 2026-10-11 10:00:00

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4a8e2f1b7d3'
down_revision: Union[str, Sequence[str], None] = '7b3e9c1d2f54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('regimen_versions') as batch_op:
        batch_op.add_column(sa.Column('day_kinds', sa.JSON(), nullable=True))

    # Each weekday takes the kind of its old primary Routine (slot 0); no Routine = Recovery.
    conn = op.get_bind()
    kinds: dict[str, list[str]] = {
        v: ['recovery'] * 7
        for (v,) in conn.execute(sa.text('SELECT id FROM regimen_versions')).fetchall()
    }
    rows = conn.execute(
        sa.text(
            'SELECT w.regimen_version_id, w.weekday, d.kind FROM week_schedule w '
            'JOIN day_types d ON d.id = w.day_type_id WHERE w.slot = 0'
        )
    ).fetchall()
    for version_id, weekday, kind in rows:
        kinds[version_id][weekday] = kind
    for version_id, week in kinds.items():
        conn.execute(
            sa.text('UPDATE regimen_versions SET day_kinds = :k WHERE id = :v'),
            {'k': json.dumps(week), 'v': version_id},
        )

    with op.batch_alter_table('regimen_versions') as batch_op:
        batch_op.alter_column('day_kinds', existing_type=sa.JSON(), nullable=False)
    with op.batch_alter_table('day_types') as batch_op:
        batch_op.drop_column('kind')


def downgrade() -> None:
    # Lossy: every Routine comes back as a Standard Routine.
    with op.batch_alter_table('day_types') as batch_op:
        batch_op.add_column(
            sa.Column('kind', sa.String(length=16), nullable=False, server_default='standard')
        )
    with op.batch_alter_table('regimen_versions') as batch_op:
        batch_op.drop_column('day_kinds')

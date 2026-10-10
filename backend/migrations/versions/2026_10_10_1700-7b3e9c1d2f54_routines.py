"""routines: up to 2 Routines (Day Types) per weekday; every-day Goals become a "Daily Routine"

Revision ID: 7b3e9c1d2f54
Revises: 5d1c0e7a9b42
Create Date: 2026-10-10 17:00:00

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision: str = '7b3e9c1d2f54'
down_revision: Union[str, Sequence[str], None] = '5d1c0e7a9b42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid() -> str:
    # sa.Uuid on SQLite stores 32-char hex without dashes.
    return uuid4().hex


def upgrade() -> None:
    # 1. week_schedule gets a slot; the unique key becomes (version, weekday, slot).
    op.create_table(
        'week_schedule_new',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('regimen_version_id', sa.Uuid(), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=False),
        sa.Column('slot', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('day_type_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['day_type_id'], ['day_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['regimen_version_id'], ['regimen_versions.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('regimen_version_id', 'weekday', 'slot'),
    )
    op.execute(
        'INSERT INTO week_schedule_new (id, regimen_version_id, weekday, slot, day_type_id) '
        'SELECT id, regimen_version_id, weekday, 0, day_type_id FROM week_schedule'
    )
    op.drop_table('week_schedule')
    op.rename_table('week_schedule_new', 'week_schedule')

    # 2. Each version's every-day Goals -> a "Daily Routine" in slot 1 of every weekday.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text('SELECT regimen_version_id, goal_id FROM every_day_goals')
    ).fetchall()
    by_version: dict[str, list[str]] = {}
    for version_id, goal_id in rows:
        by_version.setdefault(version_id, []).append(goal_id)
    for version_id, goal_ids in by_version.items():
        sort = conn.execute(
            sa.text('SELECT COALESCE(MAX(sort), -1) + 1 FROM day_types WHERE regimen_version_id = :v'),
            {'v': version_id},
        ).scalar()
        routine_id = _uuid()
        conn.execute(
            sa.text(
                'INSERT INTO day_types (id, regimen_version_id, name, kind, sort) '
                "VALUES (:id, :v, 'Daily Routine', 'standard', :sort)"
            ),
            {'id': routine_id, 'v': version_id, 'sort': sort},
        )
        for i, goal_id in enumerate(goal_ids):
            conn.execute(
                sa.text(
                    'INSERT INTO day_type_goals (id, day_type_id, goal_id, target_override, sort) '
                    'VALUES (:id, :dt, :g, NULL, :sort)'
                ),
                {'id': _uuid(), 'dt': routine_id, 'g': goal_id, 'sort': i},
            )
        for weekday in range(7):
            conn.execute(
                sa.text(
                    'INSERT INTO week_schedule (id, regimen_version_id, weekday, slot, day_type_id) '
                    'VALUES (:id, :v, :w, 1, :dt)'
                ),
                {'id': _uuid(), 'v': version_id, 'w': weekday, 'dt': routine_id},
            )
    op.drop_table('every_day_goals')


def downgrade() -> None:
    # Lossy: second Routines are dropped; every-day Goals are not restored.
    op.create_table(
        'every_day_goals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('regimen_version_id', sa.Uuid(), nullable=False),
        sa.Column('goal_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['regimen_version_id'], ['regimen_versions.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'week_schedule_old',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('regimen_version_id', sa.Uuid(), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=False),
        sa.Column('day_type_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['day_type_id'], ['day_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['regimen_version_id'], ['regimen_versions.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('regimen_version_id', 'weekday'),
    )
    op.execute(
        'INSERT INTO week_schedule_old (id, regimen_version_id, weekday, day_type_id) '
        'SELECT id, regimen_version_id, weekday, day_type_id FROM week_schedule WHERE slot = 0'
    )
    op.drop_table('week_schedule')
    op.rename_table('week_schedule_old', 'week_schedule')

"""Add teacher to schedule

Revision ID: eaa5a932eb82
Revises: d6037528cc0c
Create Date: 2026-01-17 20:01:51.651452

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaa5a932eb82'
down_revision: Union[str, Sequence[str], None] = 'd6037528cc0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('teacher_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_schedules_teacher', 'users', ['teacher_id'], ['id'])
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---


def downgrade() -> None:
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.drop_constraint('fk_schedules_teacher', type_='foreignkey')
        batch_op.drop_column('teacher_id')
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---

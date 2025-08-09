"""initial

Revision ID: 1
Revises: 
Create Date: 2023-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    op.create_table('chat_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(length=1000), nullable=False),
        sa.Column('response', sa.String(length=2000), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_history_session_id'), 'chat_history', ['session_id'], unique=False)
    op.create_index(op.f('ix_chat_history_user_id'), 'chat_history', ['user_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_chat_history_user_id'), table_name='chat_history')
    op.drop_index(op.f('ix_chat_history_session_id'), table_name='chat_history')
    op.drop_table('chat_history')
    op.drop_table('users')
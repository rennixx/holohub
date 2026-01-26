"""add user settings

Revision ID: add_user_settings
Revises:
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_settings'
down_revision = None  # This will be set when the migration is created in the actual system
branch_labels = Union[str, Sequence[str], None]
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_settings table."""
    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Notification Preferences
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('push_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('device_alerts', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('playlist_updates', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('team_invites', sa.Boolean(), nullable=False, server_default='true'),

        # Display Preferences
        sa.Column('theme', sa.Enum('dark', 'light', 'system', name='theme_preference'), nullable=False, server_default='dark'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('date_format', sa.String(length=20), nullable=False, server_default='MM/DD/YYYY'),

        # Default Behaviors
        sa.Column('default_view_mode', sa.Enum('grid', 'list', name='view_mode'), nullable=False, server_default='grid'),
        sa.Column('items_per_page', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('auto_refresh_devices', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_refresh_interval', sa.Integer(), nullable=False, server_default='30'),

        # Privacy
        sa.Column('profile_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('activity_visible', sa.Boolean(), nullable=False, server_default='true'),

        # Indexes
        sa.PrimaryKeyConstraint('id', name='user_settings_pkey'),
    )

    # Create index on user_id for faster lookups
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'])

    # Create default settings for existing users
    op.execute("""
        INSERT INTO user_settings (user_id, created_at, updated_at)
        SELECT id, now(), now()
        FROM users
        WHERE NOT EXISTS (
            SELECT 1 FROM user_settings WHERE user_settings.user_id = users.id
        )
    """)


def downgrade() -> None:
    """Drop user_settings table."""
    op.drop_index('ix_user_settings_user_id', table_name='user_settings')
    op.drop_table('user_settings')

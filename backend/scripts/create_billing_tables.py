"""Create billing-related tables."""
import asyncio
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.base import get_db


async def main():
    """Create billing tables."""
    async with get_db() as db:
        # Create invoice_status enum type
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE invoice_status AS ENUM ('draft', 'open', 'paid', 'void', 'uncollectible');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        # Create invoices table
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS invoices (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                stripe_invoice_id VARCHAR(255),
                amount NUMERIC(10, 2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
                status invoice_status DEFAULT 'open' NOT NULL,
                description TEXT,
                due_date TIMESTAMP WITH TIME ZONE,
                paid_at TIMESTAMP WITH TIME ZONE,
                invoice_pdf VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                deleted_at TIMESTAMP WITH TIME ZONE
            );
        """))

        # Create indexes
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_invoices_organization_id ON invoices(organization_id);
        """))
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_invoices_stripe_invoice_id ON invoices(stripe_invoice_id);
        """))
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices(status);
        """))
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_invoices_deleted_at ON invoices(deleted_at);
        """))

        # Create user_settings table if it doesn't exist
        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE theme_preference AS ENUM ('dark', 'light', 'system');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        await db.execute(text("""
            DO $$ BEGIN
                CREATE TYPE view_mode AS ENUM ('grid', 'list');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id SERIAL PRIMARY KEY,
                user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                email_notifications BOOLEAN DEFAULT true NOT NULL,
                push_notifications BOOLEAN DEFAULT true NOT NULL,
                device_alerts BOOLEAN DEFAULT true NOT NULL,
                playlist_updates BOOLEAN DEFAULT true NOT NULL,
                team_invites BOOLEAN DEFAULT true NOT NULL,
                theme theme_preference DEFAULT 'dark' NOT NULL,
                language VARCHAR(10) DEFAULT 'en' NOT NULL,
                timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL,
                date_format VARCHAR(20) DEFAULT 'MM/DD/YYYY' NOT NULL,
                default_view_mode view_mode DEFAULT 'grid' NOT NULL,
                items_per_page INTEGER DEFAULT 20 NOT NULL,
                auto_refresh_devices BOOLEAN DEFAULT true NOT NULL,
                auto_refresh_interval INTEGER DEFAULT 30 NOT NULL,
                profile_visible BOOLEAN DEFAULT true NOT NULL,
                activity_visible BOOLEAN DEFAULT true NOT NULL
            );
        """))

        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_user_settings_user_id ON user_settings(user_id);
        """))

        # Create default settings for existing users
        await db.execute(text("""
            INSERT INTO user_settings (user_id, created_at, updated_at)
            SELECT id, now(), now()
            FROM users
            WHERE NOT EXISTS (
                SELECT 1 FROM user_settings WHERE user_settings.user_id = users.id
            )
        """))

        await db.commit()

        print("Billing tables created successfully!")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Database migration rollback script
Reverts migrations in reverse order
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 is not installed. Install it with: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed, using environment variables only")
    load_dotenv = lambda: None


class MigrationRollback:
    """Database migration rollback handler"""
    
    # Rollback SQL statements for each migration
    ROLLBACK_STATEMENTS = {
        "005_create_sync_tables": """
            DROP TABLE IF EXISTS sync.sync_metadata CASCADE;
        """,
        "004_create_notification_tables": """
            DROP TRIGGER IF EXISTS set_notification_read_at ON notifications.notifications;
            DROP TRIGGER IF EXISTS update_notification_settings_updated_at ON notifications.notification_settings;
            DROP FUNCTION IF EXISTS notifications.set_read_at_timestamp();
            DROP FUNCTION IF EXISTS notifications.update_updated_at_column();
            DROP TABLE IF EXISTS notifications.notification_settings CASCADE;
            DROP TABLE IF EXISTS notifications.notifications CASCADE;
        """,
        "003_create_iot_tables": """
            DROP TRIGGER IF EXISTS increment_dose_on_activity ON iot.activity_logs;
            DROP TRIGGER IF EXISTS update_devices_updated_at ON iot.devices;
            DROP FUNCTION IF EXISTS iot.increment_dose_counter();
            DROP FUNCTION IF EXISTS iot.update_updated_at_column();
            DROP TABLE IF EXISTS iot.activity_logs CASCADE;
            DROP TABLE IF EXISTS iot.device_states CASCADE;
            DROP TABLE IF EXISTS iot.devices CASCADE;
        """,
        "002_create_auth_tables": """
            DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON auth.user_profiles;
            DROP TRIGGER IF EXISTS update_users_updated_at ON auth.users;
            DROP FUNCTION IF EXISTS auth.update_updated_at_column();
            DROP TABLE IF EXISTS auth.password_reset_tokens CASCADE;
            DROP TABLE IF EXISTS auth.refresh_tokens CASCADE;
            DROP TABLE IF EXISTS auth.user_profiles CASCADE;
            DROP TABLE IF EXISTS auth.users CASCADE;
        """,
        "001_create_schemas": """
            DROP SCHEMA IF EXISTS sync CASCADE;
            DROP SCHEMA IF EXISTS notifications CASCADE;
            DROP SCHEMA IF EXISTS iot CASCADE;
            DROP SCHEMA IF EXISTS auth CASCADE;
        """
    }
    
    def __init__(self):
        """Initialize rollback handler"""
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
    
    def get_db_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "zinzino_iot"),
                user=os.getenv("POSTGRES_USER", "zinzino_user"),
                password=os.getenv("POSTGRES_PASSWORD", "zinzino_pass_2024")
            )
            return conn
        except psycopg2.Error as e:
            print(f"✗ Failed to connect to database: {e}")
            sys.exit(1)
    
    def get_executed_migrations(self) -> list:
        """Get list of executed migrations in reverse order"""
        try:
            self.cursor.execute("""
                SELECT version FROM schema_migrations 
                ORDER BY version DESC
            """)
            executed = [row[0] for row in self.cursor.fetchall()]
            return executed
        except psycopg2.Error:
            # Table might not exist
            return []
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        if version not in self.ROLLBACK_STATEMENTS:
            print(f"⚠ No rollback statement for {version}")
            return False
        
        try:
            print(f"→ Rolling back {version}...")
            
            # Execute rollback SQL
            rollback_sql = self.ROLLBACK_STATEMENTS[version]
            self.cursor.execute(rollback_sql)
            
            # Remove from migrations table
            self.cursor.execute(
                "DELETE FROM schema_migrations WHERE version = %s",
                (version,)
            )
            
            self.conn.commit()
            print(f"✓ Rolled back {version}")
            return True
            
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"✗ Failed to rollback {version}: {e}")
            return False
    
    def rollback_all(self):
        """Rollback all migrations"""
        print("=" * 60)
        print("Zinzino IoT Database Migration Rollback")
        print("=" * 60)
        print()
        
        # Load environment variables
        load_dotenv()
        
        # Connect to database
        print("→ Connecting to database...")
        self.conn = self.get_db_connection()
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to {os.getenv('POSTGRES_DB', 'zinzino_iot')}")
        print()
        
        try:
            # Get executed migrations
            executed = self.get_executed_migrations()
            
            if not executed:
                print("✓ No migrations to rollback")
                return
            
            print(f"Found {len(executed)} executed migration(s)")
            print()
            
            # Confirm rollback
            print("⚠ WARNING: This will rollback all migrations and delete all data!")
            response = input("Are you sure you want to continue? (yes/no): ")
            
            if response.lower() not in ['yes', 'y']:
                print("\n⊘ Rollback cancelled")
                return
            
            print()
            
            # Rollback migrations in reverse order
            success_count = 0
            for version in executed:
                if self.rollback_migration(version):
                    success_count += 1
                else:
                    print("\n⚠ Rollback stopped due to error")
                    break
            
            # Drop migrations table if all migrations rolled back
            if success_count == len(executed):
                print("→ Dropping schema_migrations table...")
                self.cursor.execute("DROP TABLE IF EXISTS schema_migrations")
                self.conn.commit()
                print("✓ Dropped schema_migrations table")
            
            print()
            print("=" * 60)
            print(f"✓ Successfully rolled back {success_count} migration(s)")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ Rollback failed: {e}")
            sys.exit(1)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
    
    def rollback_last(self, count: int = 1):
        """Rollback last N migrations"""
        print("=" * 60)
        print(f"Zinzino IoT Database Migration Rollback (Last {count})")
        print("=" * 60)
        print()
        
        # Load environment variables
        load_dotenv()
        
        # Connect to database
        print("→ Connecting to database...")
        self.conn = self.get_db_connection()
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to {os.getenv('POSTGRES_DB', 'zinzino_iot')}")
        print()
        
        try:
            # Get executed migrations
            executed = self.get_executed_migrations()
            
            if not executed:
                print("✓ No migrations to rollback")
                return
            
            # Limit to requested count
            to_rollback = executed[:min(count, len(executed))]
            
            print(f"Will rollback {len(to_rollback)} migration(s):")
            for version in to_rollback:
                print(f"  - {version}")
            print()
            
            # Confirm rollback
            response = input("Are you sure you want to continue? (yes/no): ")
            
            if response.lower() not in ['yes', 'y']:
                print("\n⊘ Rollback cancelled")
                return
            
            print()
            
            # Rollback migrations
            success_count = 0
            for version in to_rollback:
                if self.rollback_migration(version):
                    success_count += 1
                else:
                    print("\n⚠ Rollback stopped due to error")
                    break
            
            print()
            print("=" * 60)
            print(f"✓ Successfully rolled back {success_count} migration(s)")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ Rollback failed: {e}")
            sys.exit(1)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Rollback database migrations")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Rollback all migrations"
    )
    parser.add_argument(
        "--last",
        type=int,
        metavar="N",
        help="Rollback last N migrations"
    )
    
    args = parser.parse_args()
    
    rollback = MigrationRollback()
    
    if args.all:
        rollback.rollback_all()
    elif args.last:
        rollback.rollback_last(args.last)
    else:
        # Default: rollback last migration
        rollback.rollback_last(1)


if __name__ == "__main__":
    main()

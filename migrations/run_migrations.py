#!/usr/bin/env python3
"""
Database migration runner
Executes SQL migration files in order and tracks execution
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 is not installed. Install it with: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed, using environment variables only")
    load_dotenv = lambda: None


class MigrationRunner:
    """Database migration runner with tracking"""
    
    def __init__(self):
        """Initialize migration runner"""
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cursor: Optional[psycopg2.extensions.cursor] = None
        
    def get_db_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5436")),
                database=os.getenv("POSTGRES_DB", "zinzino_iot"),
                user=os.getenv("POSTGRES_USER", "zinzino_user"),
                password=os.getenv("POSTGRES_PASSWORD", "zinzino_pass_2024")
            )
            return conn
        except psycopg2.Error as e:
            print(f"✗ Failed to connect to database: {e}")
            sys.exit(1)
    
    def create_migrations_table(self):
        """Create schema_migrations table if not exists"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            self.conn.commit()
            print("✓ Schema migrations table ready")
        except psycopg2.Error as e:
            print(f"✗ Failed to create migrations table: {e}")
            self.conn.rollback()
            raise
    
    def get_executed_migrations(self) -> set:
        """Get list of already executed migrations"""
        try:
            self.cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            executed = {row[0] for row in self.cursor.fetchall()}
            return executed
        except psycopg2.Error as e:
            print(f"✗ Failed to get executed migrations: {e}")
            return set()
    
    def get_migration_files(self) -> list:
        """Get sorted list of migration files"""
        migrations_dir = Path(__file__).parent
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql")
            if f.name != "rollback.sql"  # Exclude rollback file
        ])
        return migration_files
    
    def execute_migration(self, migration_file: Path) -> bool:
        """Execute a single migration file"""
        version = migration_file.stem
        
        try:
            print(f"→ Running {version}...")
            
            # Read migration file
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Execute migration
            self.cursor.execute(sql_content)
            
            # Record migration
            self.cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,)
            )
            
            self.conn.commit()
            print(f"✓ Completed {version}")
            return True
            
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"✗ Failed {version}: {e}")
            return False
    
    def run(self):
        """Run all pending migrations"""
        print("=" * 60)
        print("Zinzino IoT Database Migration Runner")
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
            # Create migrations tracking table
            self.create_migrations_table()
            print()
            
            # Get executed migrations
            executed = self.get_executed_migrations()
            
            # Get migration files
            migration_files = self.get_migration_files()
            
            if not migration_files:
                print("✗ No migration files found")
                return
            
            print(f"Found {len(migration_files)} migration file(s)")
            print()
            
            # Execute pending migrations
            pending_count = 0
            success_count = 0
            
            for migration_file in migration_files:
                version = migration_file.stem
                
                if version in executed:
                    print(f"⊘ Skipping {version} (already executed)")
                    continue
                
                pending_count += 1
                if self.execute_migration(migration_file):
                    success_count += 1
                else:
                    print("\n✗ Migration failed, stopping execution")
                    break
            
            print()
            print("=" * 60)
            if pending_count == 0:
                print("✓ Database is up to date (no pending migrations)")
            elif success_count == pending_count:
                print(f"✓ Successfully executed {success_count} migration(s)")
            else:
                print(f"⚠ Executed {success_count}/{pending_count} migration(s)")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n✗ Migration process failed: {e}")
            sys.exit(1)
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()


def main():
    """Main entry point"""
    runner = MigrationRunner()
    runner.run()


if __name__ == "__main__":
    main()

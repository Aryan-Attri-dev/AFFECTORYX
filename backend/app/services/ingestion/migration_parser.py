import re
from typing import List
from sqlalchemy.orm import Session

from app.models.graph import (
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceSourceKind,
)
from app.services.graph_engine import GraphEngine
from app.schemas.graph import SQLMigrationIngestionSummary


class SQLMigrationAnalyzer:
    @staticmethod
    def analyze_sql_migration(
        db: Session,
        organization_id: str,
        project_id: str,
        migration_filename: str,
        sql_content: str,
    ) -> SQLMigrationIngestionSummary:
        """Parse SQL migration DDL statements, track table nodes, and flag destructive operations."""
        tables_created = 0
        tables_modified = 0
        destructive_ops: List[str] = []
        edges_created = 0

        # Regex for CREATE TABLE
        create_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\"`\w\.]+)", re.IGNORECASE)
        # Regex for DROP TABLE
        drop_table_pattern = re.compile(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\"`\w\.]+)", re.IGNORECASE)
        # Regex for DROP COLUMN
        drop_col_pattern = re.compile(r"ALTER\s+TABLE\s+([\"`\w\.]+)\s+DROP\s+COLUMN\s+([\"`\w]+)", re.IGNORECASE)
        # Regex for ALTER TABLE
        alter_pattern = re.compile(r"ALTER\s+TABLE\s+([\"`\w\.]+)", re.IGNORECASE)

        for match in create_pattern.finditer(sql_content):
            raw_table = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            tables_created += 1
            node = GraphEngine.get_or_create_node(
                db=db,
                organization_id=organization_id,
                project_id=project_id,
                node_type=NodeType.DATABASE_TABLE,
                identifier=f"table:{raw_table}",
                name=raw_table,
                description=f"Database table defined in {migration_filename}",
            )

        for match in drop_table_pattern.finditer(sql_content):
            raw_table = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            destructive_ops.append(f"DROP TABLE {raw_table}")

        for match in drop_col_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            col_name = match.group(2).replace('"', '').replace('`', '')
            destructive_ops.append(f"ALTER TABLE {table_name} DROP COLUMN {col_name}")

        for match in alter_pattern.finditer(sql_content):
            tables_modified += 1

        db.commit()

        return SQLMigrationIngestionSummary(
            tables_created=tables_created,
            tables_modified=tables_modified,
            destructive_operations=destructive_ops,
            edges_created=edges_created,
        )

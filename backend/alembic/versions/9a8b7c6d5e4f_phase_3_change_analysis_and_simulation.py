"""phase_3_change_analysis_and_simulation

Revision ID: 9a8b7c6d5e4f
Revises: 43668c38352e
Create Date: 2026-11-02 20:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a8b7c6d5e4f'
down_revision: Union[str, None] = '43668c38352e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'change_analyses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('analysis_type', sa.String(length=50), nullable=False),
        sa.Column('base_version', sa.String(length=100), nullable=False),
        sa.Column('target_version', sa.String(length=100), nullable=False),
        sa.Column('breaking_count', sa.Integer(), nullable=False),
        sa.Column('non_breaking_count', sa.Integer(), nullable=False),
        sa.Column('findings', sa.JSON(), nullable=False),
        sa.Column('metadata_info', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_change_analyses_id'), 'change_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_change_analyses_organization_id'), 'change_analyses', ['organization_id'], unique=False)
    op.create_index(op.f('ix_change_analyses_project_id'), 'change_analyses', ['project_id'], unique=False)
    op.create_index(op.f('ix_change_analyses_author_id'), 'change_analyses', ['author_id'], unique=False)
    op.create_index('ix_analysis_org_project', 'change_analyses', ['organization_id', 'project_id'], unique=False)

    risk_enum = sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='risklevel')
    verdict_enum = sa.Enum('SAFE', 'SAFE_WITH_MITIGATION', 'BLOCKED', 'SAFE_TO_DEPLOY', 'BREAKING_CHANGES_DETECTED', 'CAUTION_REQUIRED', name='deploymentverdict')

    op.create_table(
        'simulation_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.String(length=36), nullable=True),
        sa.Column('author_id', sa.String(length=36), nullable=True),
        sa.Column('target_component_id', sa.String(length=255), nullable=False),
        sa.Column('target_component_name', sa.String(length=255), nullable=False),
        sa.Column('risk_level', risk_enum, nullable=False),
        sa.Column('verdict', verdict_enum, nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('directly_affected_services', sa.JSON(), nullable=False),
        sa.Column('transitive_affected_services', sa.JSON(), nullable=False),
        sa.Column('affected_customers', sa.JSON(), nullable=False),
        sa.Column('spof_identified', sa.JSON(), nullable=False),
        sa.Column('has_unknown_dependencies', sa.Integer(), nullable=False),
        sa.Column('verification_checklist', sa.JSON(), nullable=False),
        sa.Column('markdown_report', sa.Text(), nullable=False),
        sa.Column('report_details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['change_analyses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_simulation_reports_id'), 'simulation_reports', ['id'], unique=False)
    op.create_index(op.f('ix_simulation_reports_organization_id'), 'simulation_reports', ['organization_id'], unique=False)
    op.create_index(op.f('ix_simulation_reports_project_id'), 'simulation_reports', ['project_id'], unique=False)
    op.create_index(op.f('ix_simulation_reports_analysis_id'), 'simulation_reports', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_simulation_reports_author_id'), 'simulation_reports', ['author_id'], unique=False)
    op.create_index(op.f('ix_simulation_reports_target_component_id'), 'simulation_reports', ['target_component_id'], unique=False)
    op.create_index(op.f('ix_simulation_reports_risk_level'), 'simulation_reports', ['risk_level'], unique=False)
    op.create_index(op.f('ix_simulation_reports_verdict'), 'simulation_reports', ['verdict'], unique=False)
    op.create_index('ix_sim_org_project', 'simulation_reports', ['organization_id', 'project_id'], unique=False)


def downgrade() -> None:
    op.drop_table('simulation_reports')
    op.drop_table('change_analyses')

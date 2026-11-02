import re
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.services.audit_service import AuditService
from app.services.org_service import slugify


class ProjectService:
    @staticmethod
    def list_projects(
        db: Session,
        organization_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProjectRead]:
        projects = (
            db.query(Project)
            .filter(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [ProjectRead.model_validate(p) for p in projects]

    @staticmethod
    def get_project(
        db: Session,
        organization_id: str,
        project_id_or_slug: str,
    ) -> Project:
        project = (
            db.query(Project)
            .filter(
                Project.organization_id == organization_id,
                (Project.id == project_id_or_slug) | (Project.slug == project_id_or_slug),
            )
            .first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found in this organization",
            )
        return project

    @staticmethod
    def create_project(
        db: Session,
        organization_id: str,
        data: ProjectCreate,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> Project:
        base_slug = slugify(data.slug or data.name)
        slug = base_slug
        counter = 1
        while (
            db.query(Project)
            .filter(Project.organization_id == organization_id, Project.slug == slug)
            .first()
        ):
            slug = f"{base_slug}-{counter}"
            counter += 1

        project = Project(
            organization_id=organization_id,
            name=data.name,
            slug=slug,
            description=data.description,
            repository_url=data.repository_url,
            default_branch=data.default_branch,
            environments=data.environments,
            metadata_info=data.metadata_info,
        )
        db.add(project)
        db.flush()

        AuditService.log(
            db=db,
            organization_id=organization_id,
            user_id=actor.id,
            action="project.create",
            target_type="project",
            target_id=project.id,
            details={"name": project.name, "slug": project.slug},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update_project(
        db: Session,
        organization_id: str,
        project_id: str,
        data: ProjectUpdate,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> Project:
        project = ProjectService.get_project(db, organization_id, project_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(project, key, val)

        AuditService.log(
            db=db,
            organization_id=organization_id,
            user_id=actor.id,
            action="project.update",
            target_type="project",
            target_id=project.id,
            details={"updated_fields": list(update_dict.keys())},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(
        db: Session,
        organization_id: str,
        project_id: str,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> None:
        project = ProjectService.get_project(db, organization_id, project_id)
        project_id_saved = project.id
        project_name = project.name

        db.delete(project)
        AuditService.log(
            db=db,
            organization_id=organization_id,
            user_id=actor.id,
            action="project.delete",
            target_type="project",
            target_id=project_id_saved,
            details={"name": project_name},
            ip_address=ip_address,
        )
        db.commit()

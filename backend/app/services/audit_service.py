from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogRead


class AuditService:
    @staticmethod
    def log(
        db: Session,
        organization_id: str,
        action: str,
        user_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def get_organization_logs(
        db: Session,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLogRead]:
        records = (
            db.query(AuditLog)
            .filter(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        results = []
        for r in records:
            results.append(
                AuditLogRead(
                    id=r.id,
                    organization_id=r.organization_id,
                    user_id=r.user_id,
                    user_email=r.user.email if r.user else None,
                    user_name=r.user.full_name if r.user else None,
                    action=r.action,
                    target_type=r.target_type,
                    target_id=r.target_id,
                    details=r.details or {},
                    ip_address=r.ip_address,
                    created_at=r.created_at,
                )
            )
        return results

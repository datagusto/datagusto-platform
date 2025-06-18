from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.guardrail import Guardrail
from app.schemas.guardrail import GuardrailCreate, GuardrailUpdate


class GuardrailRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, guardrail_id: UUID) -> Optional[Guardrail]:
        """ID でガードレールを取得"""
        return self.db.query(Guardrail).filter(Guardrail.id == guardrail_id).first()

    def get_by_project_id(self, project_id: UUID) -> List[Guardrail]:
        """プロジェクトIDでガードレール一覧を取得"""
        return self.db.query(Guardrail).filter(
            Guardrail.project_id == project_id
        ).order_by(Guardrail.created_at.desc()).all()

    def get_active_by_project_id(self, project_id: UUID) -> List[Guardrail]:
        """プロジェクトIDでアクティブなガードレール一覧を取得"""
        return self.db.query(Guardrail).filter(
            and_(
                Guardrail.project_id == project_id,
                Guardrail.is_active == True
            )
        ).order_by(Guardrail.created_at.desc()).all()

    def create(self, project_id: UUID, guardrail_data: GuardrailCreate) -> Guardrail:
        """ガードレールを作成"""
        db_guardrail = Guardrail(
            project_id=project_id,
            name=guardrail_data.name,
            description=guardrail_data.description,
            trigger_condition=guardrail_data.trigger_condition.model_dump(),
            check_config=guardrail_data.check_config.model_dump(),
            action=guardrail_data.action.model_dump(),
            is_active=guardrail_data.is_active,
        )
        self.db.add(db_guardrail)
        self.db.commit()
        self.db.refresh(db_guardrail)
        return db_guardrail

    def update(self, guardrail_id: UUID, guardrail_data: GuardrailUpdate) -> Optional[Guardrail]:
        """ガードレールを更新"""
        db_guardrail = self.get_by_id(guardrail_id)
        if not db_guardrail:
            return None

        update_data = guardrail_data.model_dump(exclude_unset=True)
        
        # JSON フィールドの特別な処理
        if 'trigger_condition' in update_data and update_data['trigger_condition']:
            update_data['trigger_condition'] = update_data['trigger_condition'].model_dump()
        if 'check_config' in update_data and update_data['check_config']:
            update_data['check_config'] = update_data['check_config'].model_dump()
        if 'action' in update_data and update_data['action']:
            update_data['action'] = update_data['action'].model_dump()

        for field, value in update_data.items():
            setattr(db_guardrail, field, value)

        self.db.commit()
        self.db.refresh(db_guardrail)
        return db_guardrail

    def delete(self, guardrail_id: UUID) -> bool:
        """ガードレールを削除"""
        db_guardrail = self.get_by_id(guardrail_id)
        if not db_guardrail:
            return False

        self.db.delete(db_guardrail)
        self.db.commit()
        return True

    def update_execution_stats(self, guardrail_id: UUID, executed: bool = True, applied: bool = False) -> Optional[Guardrail]:
        """実行統計を更新"""
        db_guardrail = self.get_by_id(guardrail_id)
        if not db_guardrail:
            return None

        if executed:
            db_guardrail.execution_count += 1
        if applied:
            db_guardrail.applied_count += 1

        self.db.commit()
        self.db.refresh(db_guardrail)
        return db_guardrail
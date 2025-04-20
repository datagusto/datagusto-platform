from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import uuid

from app.models.agent import Agent as AgentModel, AgentStatus


class AgentRepository:
    """Repository for database agent operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> AgentModel:
        """
        Create a new agent in the database.
        
        Args:
            agent_data: Agent data
            
        Returns:
            Created agent
        """
        db_agent = AgentModel(**agent_data)
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        return db_agent
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentModel]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent or None if not found
        """
        return self.db.query(AgentModel).filter(AgentModel.id == agent_id).first()
    
    async def get_agent_by_api_key(self, api_key: str) -> Optional[AgentModel]:
        """
        Get an agent by API key.
        
        Args:
            api_key: Agent API key
            
        Returns:
            Agent or None if not found
        """
        return self.db.query(AgentModel).filter(AgentModel.api_key == api_key).first()
    
    async def get_agents_by_organization_id(self, organization_id: str) -> List[AgentModel]:
        """
        Get all agents for an organization.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of agents
        """
        return self.db.query(AgentModel).filter(AgentModel.organization_id == organization_id).all()
    
    async def get_agents_by_creator_id(self, creator_id: str) -> List[AgentModel]:
        """
        Get all agents created by a specific user.
        
        Args:
            creator_id: Creator (User) ID
            
        Returns:
            List of agents
        """
        return self.db.query(AgentModel).filter(AgentModel.creator_id == creator_id).all()
    
    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[AgentModel]:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            agent_data: Agent data to update
            
        Returns:
            Updated agent or None if not found
        """
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        for key, value in agent_data.items():
            setattr(agent, key, value)
        
        self.db.commit()
        self.db.refresh(agent)
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if deleted, False if not found
        """
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            return False
        
        self.db.delete(agent)
        self.db.commit()
        return True
        
    async def generate_api_key(self) -> str:
        """
        Generate a unique API key for an agent.
        
        Returns:
            API key
        """
        while True:
            api_key = f"sk-dg-{uuid.uuid4().hex}"
            exists = await self.get_agent_by_api_key(api_key)
            if not exists:
                return api_key 
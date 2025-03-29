from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.models.agent import Agent as AgentModel, AgentStatus
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.repositories.agent_repository import AgentRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository


class AgentService:
    """Service for agent operations."""
    
    @staticmethod
    async def create_agent(user_id: str, organization_id: str, agent_data: Dict[str, Any], db: Session) -> AgentModel:
        """
        Create a new agent.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            agent_data: Agent data
            db: Database session
            
        Returns:
            Created agent
        """
        try:
            # Check if user is a member of the organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, organization_id)
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to create an agent in this organization"
                )
            
            # Only OWNER and ADMIN roles can create agents
            if member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to create an agent"
                )
            
            # Initialize repository
            agent_repo = AgentRepository(db)
            
            # Generate API key
            api_key = await agent_repo.generate_api_key()
            
            # Create agent
            agent_data_with_defaults = {
                "organization_id": organization_id,
                "creator_id": user_id,
                "api_key": api_key,
                "status": AgentStatus.ACTIVE,
                **agent_data
            }
            
            agent = await agent_repo.create_agent(agent_data_with_defaults)
            return agent
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create agent: {str(e)}"
            )
    
    @staticmethod
    async def get_agent(agent_id: str, user_id: str, db: Session) -> AgentModel:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            db: Database session
            
        Returns:
            Agent
        """
        try:
            # Initialize repository
            agent_repo = AgentRepository(db)
            
            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this agent"
                )
            
            return agent
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get agent: {str(e)}"
            )
    
    @staticmethod
    async def get_agents(user_id: str, organization_id: str, db: Session) -> List[AgentModel]:
        """
        Get all agents for an organization.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            db: Database session
            
        Returns:
            List of agents
        """
        try:
            # Check if user is a member of the organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, organization_id)
            
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access agents in this organization"
                )
            
            # Initialize repository
            agent_repo = AgentRepository(db)
            
            # Get agents
            agents = await agent_repo.get_agents_by_organization_id(organization_id)
            return agents
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get agents: {str(e)}"
            )
    
    @staticmethod
    async def get_agents_by_creator(user_id: str, db: Session) -> List[AgentModel]:
        """
        Get all agents created by a user.
        
        Args:
            user_id: User ID (creator)
            db: Database session
            
        Returns:
            List of agents
        """
        try:
            # Initialize repository
            agent_repo = AgentRepository(db)
            
            # Get agents
            agents = await agent_repo.get_agents_by_creator_id(user_id)
            return agents
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get agents: {str(e)}"
            )
    
    @staticmethod
    async def update_agent(agent_id: str, user_id: str, agent_data: Dict[str, Any], db: Session) -> AgentModel:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            agent_data: Agent data to update
            db: Database session
            
        Returns:
            Updated agent
        """
        try:
            # Initialize repositories
            agent_repo = AgentRepository(db)
            
            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Check if user is a member of the agent's organization with appropriate role
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)
            
            if not member or member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update this agent"
                )
            
            # Remove fields that should not be updated directly
            if "api_key" in agent_data:
                del agent_data["api_key"]
            if "organization_id" in agent_data:
                del agent_data["organization_id"]
            
            # Update agent
            updated_agent = await agent_repo.update_agent(agent_id, agent_data)
            return updated_agent
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update agent: {str(e)}"
            )
    
    @staticmethod
    async def delete_agent(agent_id: str, user_id: str, db: Session) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            db: Database session
            
        Returns:
            True if deleted
        """
        try:
            # Initialize repositories
            agent_repo = AgentRepository(db)
            
            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Check if user is a member of the agent's organization with appropriate role
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)
            
            if not member or member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to delete this agent"
                )
            
            # Delete agent
            success = await agent_repo.delete_agent(agent_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete agent: {str(e)}"
            )
    
    @staticmethod
    async def regenerate_api_key(agent_id: str, user_id: str, db: Session) -> dict:
        """
        Regenerate API key for an agent.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            db: Database session
            
        Returns:
            Dict with new API key
        """
        try:
            # Initialize repositories
            agent_repo = AgentRepository(db)
            
            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Check if user is a member of the agent's organization with appropriate role
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)
            
            if not member or member.role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to regenerate API key for this agent"
                )
            
            # Generate new API key
            new_api_key = await agent_repo.generate_api_key()
            
            # Update agent
            agent_data = {"api_key": new_api_key}
            await agent_repo.update_agent(agent_id, agent_data)
            
            return {"api_key": new_api_key}
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to regenerate API key: {str(e)}"
            ) 
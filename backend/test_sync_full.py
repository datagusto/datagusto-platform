#!/usr/bin/env python3
"""
Test script for full Langfuse sync process - fetch traces and save to database.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.repositories.langfuse_repository import LangfuseRepository
from app.services.trace_service import TraceService
from app.models.trace import Trace, Observation
from app.models.project import Project
from app.models.organization import Organization
from app.models.user import User
from app.core.database import Base


async def create_test_project(db_session):
    """Create a test project for sync testing."""
    
    # Create test user
    test_user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        hashed_password="dummy"
    )
    db_session.add(test_user)
    
    # Create test organization
    test_org = Organization(
        id=uuid4(),
        name="Test Organization",
        slug="test-org"
    )
    db_session.add(test_org)
    
    # Create test project with Langfuse config
    test_project = Project(
        id=uuid4(),
        name="Test Langfuse Project",
        organization_id=test_org.id,
        api_key=f"test-api-key-{uuid4()}",
        platform_type="langfuse",
        platform_config={
            "public_key": "pk-lf-586f8ee7-13e4-40ff-9025-ea9e830f7474",
            "secret_key": "sk-lf-3f589677-1efb-4c5d-af66-a0fccf2f7795",
            "url": "https://cloud.langfuse.com"
        }
    )
    db_session.add(test_project)
    
    db_session.commit()
    
    return test_project, test_user


async def test_full_sync():
    """Test the complete sync process from Langfuse to database."""
    
    # Database setup
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/datagusto"
    engine = create_engine(DATABASE_URL)
    
    # Apply migrations manually since Docker has issues
    print("🔄 Creating database tables...")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db_session:
            print("🏗️  Creating test project...")
            
            # Create test project
            test_project, test_user = await create_test_project(db_session)
            
            print(f"✅ Created test project: {test_project.id}")
            print(f"   - Organization: {test_project.organization_id}")
            print(f"   - Platform: {test_project.platform_type}")
            
            # Test sync process
            print("\n🔄 Starting Langfuse sync...")
            
            sync_result = await TraceService.sync_traces(
                project_id=str(test_project.id),
                user_id=str(test_user.id),
                db=db_session
            )
            
            print(f"✅ Sync completed!")
            print(f"   - Total traces: {sync_result.total_traces}")
            print(f"   - New traces: {sync_result.new_traces}")
            print(f"   - Updated traces: {sync_result.updated_traces}")
            print(f"   - Started at: {sync_result.sync_started_at}")
            print(f"   - Completed at: {sync_result.sync_completed_at}")
            
            if sync_result.error:
                print(f"   - Error: {sync_result.error}")
                return False
            
            # Verify data in database
            print("\n🔍 Verifying synced data...")
            
            traces = db_session.query(Trace).filter(
                Trace.project_id == test_project.id
            ).all()
            
            print(f"📊 Found {len(traces)} traces in database")
            
            if traces:
                sample_trace = traces[0]
                print(f"\n📋 Sample trace in database:")
                print(f"   - ID: {sample_trace.id}")
                print(f"   - External ID: {sample_trace.external_id}")
                print(f"   - Platform: {sample_trace.platform_type}")
                print(f"   - Timestamp: {sample_trace.timestamp}")
                print(f"   - Raw data keys: {list(sample_trace.raw_data.keys()) if sample_trace.raw_data else 'None'}")
                
                # Check observations
                observations = db_session.query(Observation).filter(
                    Observation.trace_id == sample_trace.id
                ).all()
                
                print(f"   - Observations: {len(observations)}")
                
                if observations:
                    sample_obs = observations[0]
                    print(f"     - Sample obs ID: {sample_obs.external_id}")
                    print(f"     - Sample obs type: {sample_obs.raw_data.get('type') if sample_obs.raw_data else 'Unknown'}")
                
                # Test platform adapter
                print(f"\n🔧 Testing platform adapter...")
                from app.core.platform_adapters import get_trace_adapter
                
                adapter = get_trace_adapter(sample_trace.platform_type, sample_trace.raw_data)
                print(f"   - Adapter name: {adapter.get_name()}")
                print(f"   - Adapter user_id: {adapter.get_user_id()}")
                print(f"   - Adapter session_id: {adapter.get_session_id()}")
                print(f"   - Adapter input type: {type(adapter.get_input_data())}")
                print(f"   - Adapter output type: {type(adapter.get_output_data())}")
            
            print("\n✅ Full sync test completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_sync())
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script for LangfuseRepository to verify real API access.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.repositories.langfuse_repository import LangfuseRepository


async def test_langfuse_connection():
    """Test connection to Langfuse API."""
    
    # Get credentials from environment variables or command line args
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY") 
    server_url = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # Try command line arguments if env vars not set
    if len(sys.argv) >= 3:
        public_key = sys.argv[1]
        secret_key = sys.argv[2]
        if len(sys.argv) >= 4:
            server_url = sys.argv[3]
    
    if not public_key or not secret_key:
        print("❌ Public key and secret key are required")
        print("Usage:")
        print("  uv run test_langfuse.py <public_key> <secret_key> [server_url]")
        print("Or set environment variables:")
        print("  export LANGFUSE_PUBLIC_KEY=your_key")
        print("  export LANGFUSE_SECRET_KEY=your_secret")
        print("  export LANGFUSE_HOST=https://cloud.langfuse.com")
        return False
    
    print(f"\n🔄 Testing connection to {server_url}")
    print(f"📝 Using public key: {public_key[:8]}...")
    
    try:
        # Initialize repository
        langfuse_repo = LangfuseRepository(
            public_key=public_key,
            secret_key=secret_key,
            server=server_url
        )
        
        # Test 1: Fetch recent traces
        print("\n📊 Test 1: Fetching recent traces...")
        from_timestamp = datetime.now() - timedelta(days=7)  # Last 7 days
        
        traces = langfuse_repo.get_traces(
            from_timestamp=from_timestamp,
            page=1,
            limit=5
        )
        
        print(f"✅ Successfully fetched {len(traces)} traces")
        
        if traces:
            # Show sample trace data
            sample_trace = traces[0]
            print(f"\n📋 Sample trace data structure:")
            print(f"   - ID: {sample_trace.get('id')}")
            print(f"   - Name: {sample_trace.get('name')}")
            print(f"   - Timestamp: {sample_trace.get('timestamp')}")
            print(f"   - User ID: {sample_trace.get('userId')}")
            print(f"   - Session ID: {sample_trace.get('sessionId')}")
            print(f"   - Input: {type(sample_trace.get('input'))} ({len(str(sample_trace.get('input', ''))) if sample_trace.get('input') else 0} chars)")
            print(f"   - Output: {type(sample_trace.get('output'))} ({len(str(sample_trace.get('output', ''))) if sample_trace.get('output') else 0} chars)")
            print(f"   - Usage: {sample_trace.get('usage')}")
            
            # Test 2: Fetch observations for the first trace
            print(f"\n🔍 Test 2: Fetching observations for trace {sample_trace['id']}...")
            
            observations = langfuse_repo.get_observations(
                trace_id=sample_trace['id'],
                limit=10
            )
            
            print(f"✅ Successfully fetched {len(observations)} observations")
            
            if observations:
                sample_obs = observations[0]
                print(f"\n📋 Sample observation data structure:")
                print(f"   - ID: {sample_obs.get('id')}")
                print(f"   - Name: {sample_obs.get('name')}")
                print(f"   - Type: {sample_obs.get('type')}")
                print(f"   - Start Time: {sample_obs.get('startTime')}")
                print(f"   - End Time: {sample_obs.get('endTime')}")
                print(f"   - Model: {sample_obs.get('model')}")
                print(f"   - Input: {type(sample_obs.get('input'))} ({len(str(sample_obs.get('input', ''))) if sample_obs.get('input') else 0} chars)")
                print(f"   - Output: {type(sample_obs.get('output'))} ({len(str(sample_obs.get('output', ''))) if sample_obs.get('output') else 0} chars)")
                print(f"   - Usage: {sample_obs.get('usage')}")
            
            # Test 3: Test individual trace fetch
            print(f"\n🎯 Test 3: Fetching individual trace {sample_trace['id']}...")
            
            individual_trace = langfuse_repo.get_trace(sample_trace['id'])
            print(f"✅ Successfully fetched individual trace")
            print(f"   - Match: {individual_trace['id'] == sample_trace['id']}")
            
        else:
            print("ℹ️  No traces found in the last 7 days")
            
            # Try fetching traces from last 30 days
            print("\n🔄 Trying last 30 days...")
            from_timestamp = datetime.now() - timedelta(days=30)
            traces = langfuse_repo.get_traces(
                from_timestamp=from_timestamp,
                page=1,
                limit=5
            )
            print(f"📊 Found {len(traces)} traces in last 30 days")
            
            # Show sample data if found
            if traces:
                sample_trace = traces[0]
                print(f"\n📋 Sample trace data structure:")
                print(f"   - ID: {sample_trace.get('id')}")
                print(f"   - Name: {sample_trace.get('name')}")
                print(f"   - Timestamp: {sample_trace.get('timestamp')}")
                print(f"   - User ID: {sample_trace.get('userId')}")
                print(f"   - Session ID: {sample_trace.get('sessionId')}")
                print(f"   - Input: {type(sample_trace.get('input'))} ({len(str(sample_trace.get('input', ''))) if sample_trace.get('input') else 0} chars)")
                print(f"   - Output: {type(sample_trace.get('output'))} ({len(str(sample_trace.get('output', ''))) if sample_trace.get('output') else 0} chars)")
                print(f"   - Usage: {sample_trace.get('usage')}")
                
                # Test observations for this trace
                print(f"\n🔍 Test 2: Fetching observations for trace {sample_trace['id']}...")
                observations = langfuse_repo.get_observations(
                    trace_id=sample_trace['id'],
                    limit=10
                )
                print(f"✅ Successfully fetched {len(observations)} observations")
                
                if observations:
                    sample_obs = observations[0]
                    print(f"\n📋 Sample observation data structure:")
                    print(f"   - ID: {sample_obs.get('id')}")
                    print(f"   - Name: {sample_obs.get('name')}")
                    print(f"   - Type: {sample_obs.get('type')}")
                    print(f"   - Start Time: {sample_obs.get('startTime')}")
                    print(f"   - End Time: {sample_obs.get('endTime')}")
                    print(f"   - Model: {sample_obs.get('model')}")
                    print(f"   - Input: {type(sample_obs.get('input'))} ({len(str(sample_obs.get('input', ''))) if sample_obs.get('input') else 0} chars)")
                    print(f"   - Output: {type(sample_obs.get('output'))} ({len(str(sample_obs.get('output', ''))) if sample_obs.get('output') else 0} chars)")
                    print(f"   - Usage: {sample_obs.get('usage')}")
                
                # Test individual trace fetch
                print(f"\n🎯 Test 3: Fetching individual trace {sample_trace['id']}...")
                individual_trace = langfuse_repo.get_trace(sample_trace['id'])
                print(f"✅ Successfully fetched individual trace")
                print(f"   - Match: {individual_trace['id'] == sample_trace['id']}")
        
        print("\n✅ All tests passed! LangfuseRepository is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_langfuse_connection())
    sys.exit(0 if success else 1)
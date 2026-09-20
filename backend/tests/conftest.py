import pytest
import asyncio
from app.engine.commitment_store import CommitmentStore

# Singleton store for all tests to prevent rate-limiting on Groq API
_GLOBAL_STORE = None

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def shared_store():
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = CommitmentStore()
        
        async def _build():
            await _GLOBAL_STORE.build()
            
        asyncio.run(_build())
    return _GLOBAL_STORE

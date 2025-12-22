import asyncio
import os
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page
from typing import AsyncGenerator
import subprocess
import time
import requests
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import dotenv

dotenv.load_dotenv()

# Test database configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/test_events_db")
BASE_URL = "http://localhost:8000"

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """Create a fresh database session for each test"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture(scope="session")
async def server_process():
    """Start the FastAPI server for integration tests"""
    # Set test environment
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    
    # Start the server
    process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03"
    )
    
    # Wait for server to start
    for _ in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                break
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(1)
    else:
        process.terminate()
        raise RuntimeError("Server failed to start")
    
    yield process
    
    # Clean up
    process.terminate()
    process.wait()

@pytest_asyncio.fixture(scope="session")
async def playwright_instance() -> AsyncGenerator[Playwright, None]:
    """Create a Playwright instance for the test session"""
    async with async_playwright() as playwright:
        yield playwright

@pytest_asyncio.fixture(scope="session")
async def browser(playwright_instance: Playwright) -> AsyncGenerator[Browser, None]:
    """Create a browser instance for the test session"""
    browser = await playwright_instance.chromium.launch(headless=True)
    yield browser
    await browser.close()

@pytest_asyncio.fixture(scope="function")
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create a fresh browser context for each test"""
    context = await browser.new_context()
    yield context
    await context.close()

@pytest_asyncio.fixture(scope="function")
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create a fresh page for each test"""
    page = await context.new_page()
    yield page
    await page.close()

@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    import httpx
    return httpx

@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "name": "Test Event",
        "description": "This is a test event",
        "location": "Test Location",
        "start_date": "2024-12-25T10:00:00",
        "end_date": "2024-12-25T18:00:00"
    }

@pytest.fixture
def sample_event_data_list():
    """Multiple sample events for list testing"""
    return [
        {
            "name": "Tech Conference 2024",
            "description": "Annual technology conference",
            "location": "San Francisco, CA",
            "start_date": "2024-12-20T09:00:00",
            "end_date": "2024-12-20T17:00:00"
        },
        {
            "name": "Music Festival",
            "description": "Outdoor music festival",
            "location": "Austin, TX",
            "start_date": "2024-12-22T12:00:00",
            "end_date": "2024-12-22T23:00:00"
        },
        {
            "name": "Food Fair",
            "description": "Local food vendors showcase",
            "location": "New York, NY",
            "start_date": "2024-12-24T11:00:00",
            "end_date": "2024-12-24T20:00:00"
        }
    ]

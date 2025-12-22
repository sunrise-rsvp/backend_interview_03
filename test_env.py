"""
Environment setup for integration tests
"""
import os
import asyncio
import subprocess
import time
import requests
import signal
import sys
from pathlib import Path


class TestEnvironment:
    """Manages test environment setup and teardown"""
    
    def __init__(self):
        self.processes = []
        self.base_url = "http://localhost:8000"
        self.test_db_url = "postgresql+asyncpg://postgres:password@localhost:5432/test_events_db"
        
    def setup_environment_variables(self):
        """Set up environment variables for testing"""
        os.environ.update({
            "DATABASE_URL": self.test_db_url,
            "REDIS_URL": "redis://localhost:6379",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "",
            "ENVIRONMENT": "test",
            "DEBUG": "true"
        })
        
    def start_redis_server(self):
        """Start Redis server if not running"""
        try:
            # Check if Redis is already running
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis server is already running")
            return True
        except:
            print("❌ Redis server is not running")
            print("Please start Redis server: redis-server")
            return False
            
    def start_database_server(self):
        """Check PostgreSQL database availability"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="postgres",
                password="password"
            )
            conn.close()
            print("✅ PostgreSQL server is running")
            return True
        except:
            print("❌ PostgreSQL server is not running or not accessible")
            print("Please start PostgreSQL and ensure test database exists")
            return False
            
    def create_test_database(self):
        """Create test database if it doesn't exist"""
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="postgres", 
                password="password"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Create test database
            try:
                cursor.execute("CREATE DATABASE test_events_db")
                print("✅ Created test database: test_events_db")
            except psycopg2.errors.DuplicateDatabase:
                print("✅ Test database already exists: test_events_db")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test database: {e}")
            return False
            
    def run_database_migrations(self):
        """Run database migrations for test database"""
        try:
            # Set test database URL
            os.environ["DATABASE_URL"] = self.test_db_url
            
            # Run Alembic migrations
            process = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03",
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                print("✅ Database migrations completed successfully")
                return True
            else:
                print(f"❌ Migration failed: {process.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to run migrations: {e}")
            return False
            
    def start_fastapi_server(self):
        """Start FastAPI server for testing"""
        try:
            # Start the server
            process = subprocess.Popen(
                [
                    "uvicorn", 
                    "main:app", 
                    "--host", "127.0.0.1", 
                    "--port", "8000",
                    "--log-level", "error"
                ],
                cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03"
            )
            
            self.processes.append(process)
            
            # Wait for server to start
            for i in range(30):
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        print("✅ FastAPI server started successfully")
                        return True
                except (requests.ConnectionError, requests.Timeout):
                    time.sleep(1)
                    
            print("❌ FastAPI server failed to start")
            self.cleanup()
            return False
            
        except Exception as e:
            print(f"❌ Failed to start FastAPI server: {e}")
            return False
            
    def start_celery_worker(self):
        """Start Celery worker for background tasks"""
        try:
            process = subprocess.Popen(
                [
                    "celery", 
                    "-A", "celery_worker.celery_app", 
                    "worker", 
                    "--loglevel=error",
                    "--concurrency=1"
                ],
                cwd="/Users/computer/Software-Python-Projects/microservices/backend_interview_03"
            )
            
            self.processes.append(process)
            print("✅ Celery worker started")
            return True
            
        except Exception as e:
            print(f"⚠️ Celery worker not started: {e}")
            # Not critical for basic tests
            return True
            
    def setup_full_stack(self):
        """Set up complete test environment"""
        print("🚀 Setting up test environment...")
        
        self.setup_environment_variables()
        
        if not self.start_redis_server():
            return False
            
        if not self.start_database_server():
            return False
            
        if not self.create_test_database():
            return False
            
        if not self.run_database_migrations():
            return False
            
        if not self.start_fastapi_server():
            return False
            
        self.start_celery_worker()
        
        print("✅ Test environment setup complete!")
        return True
        
    def cleanup(self):
        """Clean up test environment"""
        print("🧹 Cleaning up test environment...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                
        print("✅ Test environment cleaned up")
        
    def __enter__(self):
        if self.setup_full_stack():
            return self
        else:
            raise RuntimeError("Failed to setup test environment")
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def signal_handler(signum, frame):
    """Handle interrupt signals for graceful shutdown"""
    print("\n🛑 Received interrupt signal, cleaning up...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    with TestEnvironment() as test_env:
        print("Test environment is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

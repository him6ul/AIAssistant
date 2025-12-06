"""
Main entry point for the AI Assistant.
Initializes and starts all services.
"""

import asyncio
import os
import signal
import threading
from pathlib import Path
from dotenv import load_dotenv
import yaml

from app.utils.logger import setup_logger, get_logger
from app.network import get_network_monitor
from app.tasks.storage import get_task_storage
from app.scheduler.email_scheduler import EmailScheduler
from app.scheduler.reminder_scheduler import ReminderScheduler
# Connector loader is optional - can be enabled when connectors are configured
try:
    from app.connectors.loader import load_connectors, initialize_connectors
    CONNECTORS_AVAILABLE = True
except ImportError:
    CONNECTORS_AVAILABLE = False
    load_connectors = None
    initialize_connectors = None
# Voice listener is optional (requires pyaudio)
try:
    from app.voice_listener import get_voice_listener
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    get_voice_listener = None
from app.api.server import app
import uvicorn

# Load environment variables
load_dotenv()

# Load config
config_path = Path("config/config.yaml")
config = {}
if config_path.exists():
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)


async def initialize_services():
    """
    Initialize all services.
    """
    logger = get_logger(__name__)
    logger.info("Initializing services...")
    
    # Load connectors
    # Initialize connectors if available
    if CONNECTORS_AVAILABLE and load_connectors and initialize_connectors:
        try:
            load_connectors()
            await initialize_connectors()
        except Exception as e:
            logger.warning(f"Failed to initialize connectors: {e}")
    logger.info("Connectors loaded")
    
    # Initialize database
    storage = get_task_storage()
    await storage.initialize()
    logger.info("Database initialized")
    
    # Start network monitoring
    network_monitor = get_network_monitor()
    asyncio.create_task(network_monitor.start_monitoring())
    logger.info("Network monitoring started")
    
    # Initialize schedulers
    email_config = config.get("ingestion", {}).get("email", {})
    email_scheduler = EmailScheduler(
        interval_seconds=config.get("scheduler", {}).get("email_worker_interval", 900),
        use_o365=True,
        use_imap=False,  # Configure as needed
        o365_config=email_config
    )
    
    reminder_scheduler = ReminderScheduler(
        interval_seconds=config.get("scheduler", {}).get("reminder_check_interval", 60)
    )
    
    # Start schedulers
    asyncio.create_task(email_scheduler.start())
    asyncio.create_task(reminder_scheduler.start())
    logger.info("Schedulers started")
    
    # Initialize email notification monitor (if connectors are available)
    if CONNECTORS_AVAILABLE:
        try:
            from app.monitoring.email_monitor import EmailNotificationMonitor
            
            # Check if Gmail or Outlook are enabled
            enable_gmail = os.getenv("ENABLE_GMAIL", "false").lower() == "true"
            enable_outlook = os.getenv("ENABLE_OUTLOOK", "false").lower() == "true"
            
            # Start email monitor in separate thread with its own event loop
            # because server.serve() blocks the main event loop
            if enable_gmail or enable_outlook:
                logger.info("Starting email notification monitor in separate thread...")
                email_monitor = EmailNotificationMonitor(
                    check_interval_seconds=300,  # 5 minutes
                    lookback_minutes=5
                )
                
                def run_monitor_in_thread():
                    """Run monitor in separate thread with its own event loop."""
                    # Use asyncio.run() which properly manages the event loop lifecycle
                    try:
                        asyncio.run(email_monitor.start())
                    except Exception as e:
                        logger.error(f"Email monitor thread failed: {e}", exc_info=True)
                
                monitor_thread = threading.Thread(target=run_monitor_in_thread, daemon=True)
                monitor_thread.start()
                logger.info("Email notification monitor started in separate thread")
            else:
                logger.info("Email notification monitor skipped (Gmail and Outlook not enabled)")
        except ImportError as e:
            logger.warning(f"Email notification monitor not available: {e}")
        except Exception as e:
            logger.error(f"Failed to start email notification monitor: {e}", exc_info=True)
    
    # Initialize voice listener (optional, can be started separately)
    voice_enabled = os.getenv("VOICE_ENABLED", "false").lower() == "true"
    if voice_enabled and VOICE_AVAILABLE:
        voice_listener = get_voice_listener()
        asyncio.create_task(voice_listener.start())
        logger.info("Voice listener started")
    elif voice_enabled and not VOICE_AVAILABLE:
        logger.warning("Voice listener requested but not available (pyaudio not installed)")
    
    logger.info("All services initialized")


async def run_server():
    """
    Run the FastAPI server.
    """
    logger = get_logger(__name__)
    host = os.getenv("SERVER_HOST", "localhost")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    logger.info(f"Creating uvicorn config for {host}:{port}...")
    config_obj = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        log_config=None  # Use default logging, don't override
    )
    logger.info("Creating uvicorn Server object...")
    server = uvicorn.Server(config_obj)
    logger.info(f"About to call server.serve() on {host}:{port}...")
    try:
        await server.serve()
    except Exception as e:
        logger.error(f"Error in server.serve(): {e}", exc_info=True)
        raise


async def main():
    """
    Main function.
    """
    # Setup logging
    log_config = config.get("logging", {})
    setup_logger(
        log_level=log_config.get("level", "INFO"),
        log_file=log_config.get("file"),
        max_size_mb=log_config.get("max_size_mb", 10),
        backup_count=log_config.get("backup_count", 5)
    )
    
    logger = get_logger(__name__)
    logger.info("Starting AI Personal Assistant...")
    
    # Initialize services
    await initialize_services()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        # Cleanup would go here
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run server - ensure background tasks are scheduled first
    logger.info("Starting FastAPI server...")
    
    # Give background tasks a moment to start before server blocks
    await asyncio.sleep(0.1)
    
    # Run server (this blocks, but background tasks should run concurrently)
    logger.info("About to call run_server()...")
    try:
        await run_server()
    except Exception as e:
        logger.error(f"Error in run_server(): {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())


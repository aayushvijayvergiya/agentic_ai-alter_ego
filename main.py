"""Main entry point for the Alter Ego application."""

from src.alter_ego import create_app
from src.alter_ego.utils.logger import logger


def main():
    """Main function to run the Alter Ego application."""
    try:
        app = create_app()
        logger.info("Starting Alter Ego application...")
        app.launch()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

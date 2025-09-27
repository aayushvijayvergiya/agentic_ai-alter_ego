"""Main entry point for the Alter Ego application."""

from src.alter_ego import create_app


def main():
    """Main function to run the Alter Ego application."""
    try:
        app = create_app()
        print("Starting Alter Ego application...")
        app.launch()
    except Exception as e:
        print(f"Failed to start application: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

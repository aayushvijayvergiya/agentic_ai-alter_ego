"""Hugging Face Spaces entry point for the Alter Ego application."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from alter_ego import create_app
    from alter_ego.utils.logger import logger

    def main():
        """Main function to run the Alter Ego application on Hugging Face."""
        logger.info(f"Project root: {project_root}")
        logger.info(f"Static dir: {project_root / 'static'}")

        try:
            app = create_app()
            logger.info("Starting Alter Ego application on Hugging Face...")

            # Launch with public sharing enabled for Hugging Face
            interface = app.launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=False,  # HF handles the sharing
                show_error=True,
                quiet=False
            )

            return interface

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            import traceback
            traceback.print_exc()
            raise e

    if __name__ == "__main__":
        main()

except ImportError as e:
    # Use standard logging or print here as backup since alter_ego.utils.logger might not be importable
    print(f"Import error: {e}")
    print("Available files in current directory:")
    for item in os.listdir("."):
        print(f"  {item}")
    print(f"Python path: {sys.path}")
    raise
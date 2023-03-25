import os
from pathlib import Path

USER_DATA_DIRECTORY = os.environ.get("DATA_DIRECTORY")
DATA_DIRECTORY = Path(USER_DATA_DIRECTORY if USER_DATA_DIRECTORY else "data/")

PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
TEST_DATA_DIRECTORY = PROJECT_DIRECTORY / "tests" / "data"
SAMPLE_DUMPPAGE_CONTENT_FILE = TEST_DATA_DIRECTORY / "sample_dumppage_content"

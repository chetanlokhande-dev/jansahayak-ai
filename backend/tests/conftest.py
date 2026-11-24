import os
import sys
import tempfile
from pathlib import Path

# Make `app` importable and keep tests offline and isolated.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["GEMINI_API_KEY"] = ""
os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")

import os
import sys
import tempfile
from pathlib import Path

# Tests always use the offline brain and a throwaway database.
os.environ["AI_MODE"] = "offline"
os.environ["DEBATE_DB_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

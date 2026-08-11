import sys
from pathlib import Path

# Add src to sys.path so 'import impact...' works cleanly in pytest
root_dir = Path(__file__).parent.parent
src_dir = root_dir / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

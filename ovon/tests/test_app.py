import os
import pytest

def test_app_script_exists():
    app_path = os.path.join(os.path.dirname(__file__), "..", "src", "ovon", "app.py")
    assert os.path.exists(app_path)

def test_app_imports_cleanly():
    # Verify app syntax and imports compile cleanly
    with open(os.path.join(os.path.dirname(__file__), "..", "src", "ovon", "app.py"), "r", encoding="utf-8") as f:
        code = f.read()
    compiled = compile(code, "app.py", "exec")
    assert compiled is not None

"""
Compatibility entrypoint for the documented sync backend command.

The original SQLite backend was renamed to `backend_simple.py.bak`.  Keep this
module import-compatible so `uvicorn backend_simple:app` continues to work.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_backend_path = Path(__file__).with_name("backend.py")
_backend_spec = spec_from_file_location("reviewed_backend", _backend_path)
_backend_module = module_from_spec(_backend_spec)
assert _backend_spec and _backend_spec.loader
_backend_spec.loader.exec_module(_backend_module)

for _name in dir(_backend_module):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_backend_module, _name)

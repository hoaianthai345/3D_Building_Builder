import os
import tempfile

# Force offline, isolated artifacts for the whole test session before app import.
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("ARTIFACTS_DIR", tempfile.mkdtemp(prefix="scene-artifacts-"))

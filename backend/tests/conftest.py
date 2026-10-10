import os

# Test-only secret, long enough for HS256 (>= 32 bytes). Set before settings are first read.
os.environ.setdefault("SYSTEM_JWT_SECRET", "test-secret-0123456789abcdef0123456789")

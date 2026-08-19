"""
rate_limiter.py
===============
Rate limiting setup using slowapi, keyed by client IP address.
Used to slow down brute-force login attempts.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
from slowapi import Limiter
from slowapi.util import get_remote_address

# Single shared limiter instance imported by main.py and all routers
limiter = Limiter(key_func=get_remote_address)

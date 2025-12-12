"""
Integration API Module.

This module initializes the Integration API using the ucapi library and sets up an
Asyncio event loop. It provides a foundation for interacting with the API.

Attributes:
    loop (asyncio.BaseEventLoop): The Asyncio event loop used by the API.
    api (ucapi.IntegrationAPI): The initialized Integration API instance.
"""

import asyncio
import sys

import ucapi
from ucapi.api import IntegrationAPI

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

loop = asyncio.new_event_loop()
api: IntegrationAPI = ucapi.IntegrationAPI(loop)

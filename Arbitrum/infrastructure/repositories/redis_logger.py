"""Redis logger for pool events and states."""

import json
import time
from typing import Any, Dict, Optional, List, Union
import redis
from decimal import Decimal
"""Decimal arithmetic internally, JSON numbers for the public SPA contract."""
from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer


# Restrict this alias to response fields: model_dump() keeps Decimal for Python
# and database operations; JSON and its response schema expose a number.
JsonDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]

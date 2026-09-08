"""Shared unit-of-work lock for the enforced single API process deployment."""
from functools import wraps
from threading import RLock

mutation_lock = RLock()


def serialized_mutation(function):
    @wraps(function)
    def locked(*args, **kwargs):
        with mutation_lock:
            return function(*args, **kwargs)
    return locked

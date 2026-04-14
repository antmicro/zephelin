# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides a class for endpoints registering for automated docs generation.
"""

from typing import Callable


class Endpoints:
    """
    Class associating methods with endpoints, apps and methods.
    """

    def __init__(self):
        """
        Creates object with endpoints.
        """
        # Maps endpoint to (method, function)
        self.endpoints = {}

    def items(self):
        return self.endpoints.items()

    def register_method(self, endpoint: str) -> Callable:
        """
        Decorator registering methods as endpoints.

        Parameters
        ----------
        endpoint : str
            Name of the endpoint

        Returns
        -------
        Callable
            Decorator registering the method
        """

        def _decorator(func: Callable):
            if not hasattr(func, "__name__"):
                raise ValueError("Invalid endpoint function")
            self.endpoints[endpoint] = func
            return func

        return _decorator

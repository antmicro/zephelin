# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Module containing JSON-RPC handling logic.
"""

import logging
from typing import Any, Callable, Optional

from handlers.base import BaseHandler
from jsonrpc.exceptions import JSONRPCDispatchException
from jsonrpc.jsonrpc2 import JSONRPC20BatchRequest, JSONRPC20Request, JSONRPC20Response

logger = logging.getLogger("RPCDispatcher")


class RPCDispatcher:
    """
    Object containing and routing JSON-RPC methods for the backend.
    """

    def __init__(self):
        """
        Builds the RPCDispatcher.
        """
        self.rpc_methods: dict[str, Callable] = {}

    def register_methods(self, instance: BaseHandler, namespace: str = ""):
        """
        Registers public methods from a handler class.

        Parameters
        ----------
        instance: BaseHandler
            An instance of a handler class with implementations of RPC methods.
            Methods starting with '_' will be ignored.

        namespace: str
            Namespace in which the methods should be registered. Registered methods will
            be available at 'namespace.method_name'.
        """
        for attr_name in dir(instance):
            if attr_name.startswith("_"):
                continue

            attr_value = getattr(instance, attr_name)
            if callable(attr_value):
                method_name = f"{namespace}.{attr_name}" if namespace else attr_name
                self.rpc_methods[method_name] = attr_value
                logger.info(f"Registered RPC Method: {method_name}")

    def _create_and_log_response(
        self, req_id: Any = None, result: Any = None, error: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Helper method to log JSON-RPC responses before sending.
        """
        response_data = JSONRPC20Response(result=result, error=error, _id=req_id).data

        if error:
            logger.error(f"{response_data}")
        else:
            logger.debug(f"{response_data}")

        return response_data

    async def dispatch_rpc(self, raw_data: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Handles the raw RPC request by dispatching it the appropriate handler.

        Parameters
        ----------
        raw_data: dict[str, Any]
            Dictionary containing a formatted JSON-RPC request.

        Returns
        -------
        Optional[dict[str, Any]]
            Dictionary containing a formatted JSON-RPC response,
            or None if request was a notification.
        """
        try:
            request = JSONRPC20Request.from_data(raw_data)

            # Silences LSP warnings
            if isinstance(request, JSONRPC20BatchRequest):
                return self._create_and_log_response(
                    error={"code": -32600, "message": "Batch requests are not supported."}
                )

            if request.method not in self.rpc_methods:
                return self._create_and_log_response(
                    req_id=request._id,
                    error={"code": -32601, "message": f"Method '{request.method}' not found"},
                )

            func = self.rpc_methods[request.method]
            params = request.params or {}

            if isinstance(params, dict):
                result = await func(**params)
            else:
                result = await func(*params)

            if request.is_notification:
                logger.debug(f"RPC Notification processed (no response expected): {request.method}")
                return None

            return self._create_and_log_response(req_id=request._id, result=result)

        except JSONRPCDispatchException as e:
            req_id = raw_data.get("id") if isinstance(raw_data, dict) else None
            return self._create_and_log_response(req_id=req_id, error=e.error._data)

        except Exception as e:
            req_id = raw_data.get("id") if isinstance(raw_data, dict) else None
            return self._create_and_log_response(
                req_id=req_id, error={"code": -32000, "message": f"Server Logic Error: {str(e)}"}
            )

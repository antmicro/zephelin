# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Module containing JSON-RPC handling logic.
"""

from typing import Any, Callable, Optional

from handlers.base import BaseHandler
from jsonrpc.exceptions import JSONRPCDispatchException
from jsonrpc.jsonrpc2 import JSONRPC20BatchRequest, JSONRPC20Request, JSONRPC20Response


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
                print(f"[Dispatcher] Registered RPC Method: {method_name}")

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
                return JSONRPC20Response(
                    error={"code": -32600, "message": "Batch requests are not supported."}, _id=None
                ).data

            if request.method not in self.rpc_methods:
                return JSONRPC20Response(
                    error={"code": -32601, "message": f"Method '{request.method}' not found"},
                    _id=request._id,
                ).data

            func = self.rpc_methods[request.method]
            params = request.params or {}

            if isinstance(params, dict):
                result = await func(**params)
            else:
                result = await func(*params)

            if request.is_notification:
                return None
            return JSONRPC20Response(result=result, _id=request._id).data

        except JSONRPCDispatchException as e:
            req_id = raw_data.get("id") if isinstance(raw_data, dict) else None
            return JSONRPC20Response(error=e.error._data, _id=req_id).data

        except Exception as e:
            req_id = raw_data.get("id") if isinstance(raw_data, dict) else None
            return JSONRPC20Response(
                error={"code": -32000, "message": f"Server Logic Error: {str(e)}"}, _id=req_id
            ).data

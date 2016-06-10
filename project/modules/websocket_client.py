#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import asyncio
import ssl

import websockets

from .tap_logger import get_logger

logger = get_logger(__name__)


class WebsocketClient:
    WS_TIMEOUT = 10  # (seconds) - timeout for unresponsive socket
    WS = "ws"
    WSS = "wss"

    def __init__(self, url, origin=None, headers=None, certificate_requirement=None):

        ws_connection_params = {
            "uri": url
        }
        if origin is not None:
            ws_connection_params.update({"origin": origin})
        if headers is not None:
            ws_connection_params.update({"extra_headers": headers})
        if certificate_requirement is not None:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.verify_mode = certificate_requirement
            ws_connection_params.update({"ssl": ssl_context})
        self.ws = asyncio.get_event_loop().run_until_complete(self._create_ws_connection(ws_connection_params))

    @asyncio.coroutine
    def _create_ws_connection(self, ws_params):
        ws = yield from websockets.connect(**ws_params)
        return ws

    @asyncio.coroutine
    def _delete_ws_connection(self):
        try:
            yield from asyncio.wait_for(self.ws.close(), timeout=self.WS_TIMEOUT)
        except asyncio.TimeoutError:
            pass

    @asyncio.coroutine
    def _send(self, msg):
        yield from asyncio.wait_for(self.ws.send(msg), timeout=self.WS_TIMEOUT)

    @asyncio.coroutine
    def _recieve(self):
        output = []
        while True:
            try:
                msg = yield from asyncio.wait_for(self.ws.recv(), timeout=self.WS_TIMEOUT)
                logger.info(msg)
                output.append(msg)
            except asyncio.TimeoutError:
                logger.info("No more messages")
                break
        return output

    def close(self):
        asyncio.get_event_loop().run_until_complete(self._delete_ws_connection())

    def send(self, msg):
        asyncio.get_event_loop().run_until_complete(self._send(msg))

    def recieve(self):
        return asyncio.get_event_loop().run_until_complete(self._recieve())

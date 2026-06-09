"""gRPC client factory."""
from __future__ import annotations

import grpc


class GRPCClientFactory:
    def __init__(self):
        self._channels: dict[str, grpc.Channel] = {}

    def get_channel(self, target: str, secure: bool = False) -> grpc.Channel:
        if target not in self._channels:
            if secure:
                self._channels[target] = grpc.secure_channel(target, grpc.ssl_channel_credentials())
            else:
                self._channels[target] = grpc.insecure_channel(target)
        return self._channels[target]

    def close(self):
        for channel in self._channels.values():
            channel.close()
        self._channels.clear()

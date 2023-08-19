import importlib
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Self

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import Message

UpgradeRequestCallable = Callable[[Any], Any]
DowngradeResponseCallable = Callable[[Any], Any]


class AdaptAPIMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._config = _MiddlewareConfig.get()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path: str = request.scope["path"]
        for versioned_api, conf in self._config.versioned_apis.items():
            if path == versioned_api:
                return await self._dispatch_versioned_api(request, call_next, conf)

        return await call_next(request)

    @classmethod
    async def _dispatch_versioned_api(
        cls,
        request: Request,
        call_next: RequestResponseEndpoint,
        config: "_VersionedApiConfig",
    ) -> Response:
        request.scope["path"] = config.latest_api

        request_body = await request.json()
        for upgrade_request in config.upgrade_requests:
            request_body = upgrade_request(request_body)
        cls._set_request_body(request, request_body)

        response = await call_next(request)

        response_body = await cls._get_response_body(response)
        for downgrade_response in reversed(config.downgrade_responses):
            response_body = downgrade_response(response_body)
        cls._set_response_body(response, response_body)

        return response

    @staticmethod
    def _set_request_body(request: Request, body: Any) -> None:
        async def _receive() -> Message:
            return {
                "type": "http.request",
                "body": json.dumps(body).encode(),
                "body_more": False,
            }

        request._receive = _receive

    @staticmethod
    async def _get_response_body(response: Response) -> Any:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        return json.loads(body.decode())

    @staticmethod
    def _set_response_body(response: Response, body: Any) -> None:
        raw = json.dumps(body).encode()

        async def _body_iterator():
            yield raw

        response.body_iterator = _body_iterator()
        response.raw_headers[0] = (b"content-length", str(len(raw)).encode())


@dataclass
class _VersionedApiConfig:
    latest_api: str
    upgrade_requests: list[UpgradeRequestCallable]
    downgrade_responses: list[DowngradeResponseCallable]


@dataclass
class _MiddlewareConfig:
    versioned_apis: dict[str, _VersionedApiConfig]

    @classmethod
    def get(cls) -> Self:
        pyproject = cls._get_pyproject()
        pyproject_adaptapi = pyproject["tool"]["adaptapi"]

        versioned_apis = {}
        for latest_api, versions in pyproject_adaptapi.items():
            for version, adaptations in versions.items():
                versioned_api = latest_api.replace("latest", version)
                adaptations_modules = [importlib.import_module(a) for a in adaptations]
                versioned_apis[versioned_api] = _VersionedApiConfig(
                    latest_api=latest_api,
                    upgrade_requests=[
                        mod.upgrade_request for mod in adaptations_modules
                    ],
                    downgrade_responses=[
                        mod.downgrade_response for mod in adaptations_modules
                    ],
                )

        return cls(
            versioned_apis=versioned_apis,
        )

    @classmethod
    def _get_pyproject(cls) -> dict[str, Any]:
        lib = Path.cwd()
        while not (lib / "pyproject.toml").exists():
            lib = lib.parent
        with open(lib / "pyproject.toml", "rb") as fp:
            return tomllib.load(fp)

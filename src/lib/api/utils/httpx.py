from typing import Callable
from functools import wraps
import threading
from fastapi import FastAPI, Response, Depends
from enum import Enum
import asyncio
import swivel.common as U

import httpx
import ssl
from fastapi import FastAPI


class HTTPRestClient:
    httpxLock_: asyncio.locks.Lock = asyncio.Lock()
    """ Lock for httpx operations """
    client_: httpx.AsyncClient
    """ httpx AsyncClient instance """
    sslCtx_: ssl.SSLContext
    """ SSL context for secure connections """

    @classmethod
    async def getClient(cls) -> httpx.AsyncClient:
        funcName = f"{HTTPRestClient.__name__}.{cls.getClient.__name__}"
        prefix = funcName
        try:
            httpxClient = getattr(cls, "client_", None)
            if httpxClient is not None:
                return cls.client_

            async with cls.httpxLock_:
                httpxClient = getattr(cls, "client_", None)
                if httpxClient is None:

                    # ## Enable legacy SSL settings?
                    # isEnableLegacySSL = App.ENV_VARS.ccsp_one_time_token_endpoint_use_legacy_ssl
                    # if isEnableLegacySSL:
                    #     ## SSL ctx
                    #     ## - Enable LEGACY_SERVER_CONNECT to support older servers
                    #     cls.sslCtx_ = ssl.create_default_context()
                    #     if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
                    #         cls.sslCtx_.options |= ssl.OP_LEGACY_SERVER_CONNECT
                    #     else:
                    #         raise RuntimeError("Your Python/ssl module does not expose OP_LEGACY_SERVER_CONNECT")

                    ## Most props have default of 5seconds (very short timeouts)
                    timeout = httpx.Timeout(
                        connect=3.0,  # TCP handshake
                        read=10.0,  # response body
                        write=10.0,  # request body
                        pool=5.0,  # wait for connection from pool
                    )
                    limits = httpx.Limits(
                        max_connections=100,
                        max_keepalive_connections=20,
                        keepalive_expiry=30.0,
                    )
                    cls.client_ = httpx.AsyncClient(
                        ## Important note:
                        ## - If connecting to older servers (e.g., CCSP), enable legacy SSL settings
                        ## - In production, it MUST be set to True, i.e. verify TLS certificates
                        # verify=cls.sslCtx_ if isEnableLegacySSL else True,
                        verify=True,
                        timeout=timeout,
                        limits=limits,
                        http2=True,
                        follow_redirects=False,
                    )
                    U.logW(
                        # f"{prefix} httpx.AsyncClient created, limits={limits}, timeout={timeout}, isEnableLegacySSL={isEnableLegacySSL}"
                        f"{prefix} httpx.AsyncClient created, limits={limits}, timeout={timeout}"
                    )

            return cls.client_

        except Exception as e:
            U.throwPrefix(prefix, e)

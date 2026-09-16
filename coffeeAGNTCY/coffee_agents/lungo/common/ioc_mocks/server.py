# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

import uvicorn


def main() -> None:
    port = int(os.getenv("PORT", "9116"))
    uvicorn.run(
        "common.ioc_mocks.app:app",
        host="0.0.0.0",
        port=port,
    )


if __name__ == "__main__":
    main()

# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0


class MockStoreError(Exception):
    pass


class MockStoreNotFoundError(MockStoreError):
    pass


class MockStoreConflictError(MockStoreError):
    pass


class MockStoreValidationError(MockStoreError):
    pass

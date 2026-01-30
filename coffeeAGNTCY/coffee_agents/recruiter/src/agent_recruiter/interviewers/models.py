# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class PolicyEvaluationResult(BaseModel):
    passed: bool
    reason: str
    policy: str
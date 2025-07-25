# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class IdentityServiceApp(BaseModel):
  id: str
  name: str
  description: Optional[str] = None
  type: str
  resolverMetadataId: str
  apiKey: Optional[str] = None
  status: str
  createdAt: str
  updatedAt: str

class IdentityServiceApps(BaseModel):
  apps: List[IdentityServiceApp]

class Proof(BaseModel):
  type: str
  proofPurpose: Optional[str] = None
  proofValue: str

class Skill(BaseModel):
  description: str
  examples: List[str]
  id: str
  name: str
  tags: List[str]

class CredentialSubject(BaseModel):
  id: str
  badge: str

class VerifiableCredential(BaseModel):
  context: List[str]
  type: List[str]
  issuer: str
  credentialSubject: CredentialSubject
  id: str
  issuanceDate: str
  expirationDate: Optional[str] = None
  credentialSchema: List[Any] = []
  credentialStatus: List[Any] = []
  proof: Proof

class Badge(BaseModel):
  verifiableCredential: VerifiableCredential
  appId: str

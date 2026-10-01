# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Dependency-compatibility contract for spiffe + PyJWT.

No code in this repo imports `spiffe` directly, but `agntcy-dir` (a
transitive dependency) does, and `spiffe==0.3.1` caps PyJWT at `<2.14`
(https://pypi.org/project/spiffe), which otherwise blocks picking up
several PyJWT CVE fixes (notably CVE-2026-102268, a critical
asymmetric-key confusion bypass).

These tests exercise `spiffe.svid.jwt_svid.JwtSvid`, the only place
spiffe calls into PyJWT (`jwt.get_unverified_header` /
`jwt.decode`, both with explicit asymmetric keys and algorithms - no
JWK/PyJWKClient involved). They pin down the behavior spiffe relies on
today, so that if PyJWT is ever forced past spiffe's declared ceiling
(an override that ignores spiffe's own constraint), a regression in
that behavior shows up here instead of silently in production.
"""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from spiffe.bundle.jwt_bundle.errors import AuthorityNotFoundError
from spiffe.bundle.jwt_bundle.jwt_bundle import JwtBundle
from spiffe.spiffe_id.spiffe_id import TrustDomain
from spiffe.svid.errors import InvalidAlgorithmError, InvalidTokenError
from spiffe.svid.jwt_svid import JwtSvid

TRUST_DOMAIN = TrustDomain("example.org")
SPIFFE_ID = "spiffe://example.org/workload"
AUDIENCE = {"my-audience"}
KEY_ID = "key-1"


@pytest.fixture(scope="module")
def keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


@pytest.fixture(scope="module")
def bundle(keypair):
    _, public_key = keypair
    return JwtBundle(TRUST_DOMAIN, {KEY_ID: public_key})


def _sign(
    private_key,
    *,
    aud=None,
    exp_delta=3600,
    sub=SPIFFE_ID,
    alg="RS256",
    kid=KEY_ID,
    key=None,
):
    now = int(time.time())
    claims = {
        "sub": sub,
        "aud": list(aud if aud is not None else AUDIENCE),
        "exp": now + exp_delta,
        "iat": now,
    }
    return jwt.encode(
        claims, key if key is not None else private_key, algorithm=alg, headers={"kid": kid}
    )


class TestJwtSvidValidation:
    """Mirrors the SPIFFE JWT-SVID guarantees our dependency tree relies on."""

    def test_valid_token_round_trips(self, keypair, bundle):
        private_key, _ = keypair
        token = _sign(private_key)
        svid = JwtSvid.parse_and_validate(token, bundle, AUDIENCE)
        assert str(svid.spiffe_id) == SPIFFE_ID
        assert svid.audience == AUDIENCE

    def test_parse_insecure_does_not_require_bundle(self, keypair):
        private_key, _ = keypair
        token = _sign(private_key)
        svid = JwtSvid.parse_insecure(token, AUDIENCE)
        assert str(svid.spiffe_id) == SPIFFE_ID

    def test_expired_token_rejected(self, keypair, bundle):
        private_key, _ = keypair
        token = _sign(private_key, exp_delta=-60)
        with pytest.raises(InvalidTokenError):
            JwtSvid.parse_and_validate(token, bundle, AUDIENCE)

    def test_wrong_audience_rejected(self, keypair, bundle):
        private_key, _ = keypair
        token = _sign(private_key, aud={"someone-else"})
        with pytest.raises(InvalidTokenError):
            JwtSvid.parse_and_validate(token, bundle, AUDIENCE)

    def test_tampered_signature_rejected(self, keypair, bundle):
        private_key, _ = keypair
        token = _sign(private_key)
        header, payload, signature = token.split(".")
        tampered = f"{header}.{payload}.{signature[:-4]}AAAA"
        with pytest.raises(InvalidTokenError):
            JwtSvid.parse_and_validate(tampered, bundle, AUDIENCE)

    def test_unknown_key_id_rejected(self, keypair, bundle):
        private_key, _ = keypair
        token = _sign(private_key, kid="not-in-bundle")
        with pytest.raises(AuthorityNotFoundError):
            JwtSvid.parse_and_validate(token, bundle, AUDIENCE)

    def test_symmetric_algorithm_rejected(self, keypair, bundle):
        """SPIFFE JWT-SVID only allows RS/ES/PS (see JwtSvidValidator);
        a symmetric alg must be rejected before any key material is used.
        This is the exact confusion-attack class CVE-2026-102268 hardens
        PyJWT against, so it must keep failing closed after an upgrade.
        """
        private_key, _ = keypair
        token = _sign(private_key, alg="HS256", key="shared-secret-not-a-real-key-32-bytes-plus")
        with pytest.raises(InvalidAlgorithmError):
            JwtSvid.parse_and_validate(token, bundle, AUDIENCE)

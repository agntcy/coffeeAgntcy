# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""A2A event middleware package with a minimal public API."""

from .inflight import register_cleanup_span_processor
from .middleware import EventEmittingInterceptor, make_event_emitting_consumer

__all__ = [
	"EventEmittingInterceptor",
	"make_event_emitting_consumer",
	"register_cleanup_span_processor",
]

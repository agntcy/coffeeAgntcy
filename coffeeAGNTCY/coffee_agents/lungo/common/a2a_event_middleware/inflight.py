# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

"""Compatibility shim - canonical implementation in ``common.workflow_utils.inflight``."""

from common.workflow_utils.inflight import (
	InterceptionState,
	InFlightCleanupSpanProcessor,
	RuntimeIdAllocator,
	TraceContext,
	_otel_trace,
	current_trace_id,
	format_span_id,
	format_trace_id,
	in_flight,
	in_flight_lock,
	read_trace_context,
	register_cleanup_span_processor,
	resolve_consumer_state,
	resolve_correlation_id,
	upsert_in_flight_state,
)

__all__ = [
	"RuntimeIdAllocator",
	"InterceptionState",
	"TraceContext",
	"in_flight",
	"in_flight_lock",
	"current_trace_id",
	"format_trace_id",
	"format_span_id",
	"read_trace_context",
	"upsert_in_flight_state",
	"resolve_correlation_id",
	"resolve_consumer_state",
	"InFlightCleanupSpanProcessor",
	"register_cleanup_span_processor",
	"_otel_trace",
]

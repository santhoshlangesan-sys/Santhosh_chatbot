import os
from threading import Lock

from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from phoenix.otel import register


_setup_lock = Lock()
_tracer_provider = None
_instrumentor: OpenAIAgentsInstrumentor | None = None


def setup_phoenix_tracing() -> None:
    global _instrumentor, _tracer_provider

    with _setup_lock:
        if _instrumentor is not None:
            return

        # Send spans to the local Phoenix collector by default; the environment
        # variable lets you point at a different Phoenix deployment.
        endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "http://127.0.0.1:6006/v1/traces",
        )
        _tracer_provider = register(
            endpoint=endpoint,
            project_name="jaguars-cricket",
            batch=True,
            verbose=False,
        )

        # Bridge OpenAI Agents SDK traces (including agent and tool activity)
        # into OpenTelemetry spans that Phoenix can receive and display.
        _instrumentor = OpenAIAgentsInstrumentor()
        _instrumentor.instrument(tracer_provider=_tracer_provider)


def flush_phoenix_traces() -> None:
    # Flush buffered spans when a server or CLI run finishes so recent traces
    # are not lost while the batch exporter is waiting to send them.
    if _tracer_provider is not None:
        _tracer_provider.force_flush(timeout_millis=5_000)

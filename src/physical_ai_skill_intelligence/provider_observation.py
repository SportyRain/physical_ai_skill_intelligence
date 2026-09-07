"""Pure software-result bridge into the existing offline evaluation harness."""
from dataclasses import asdict

from .bounded_loop import ExecutionObservation
from .provider_contract import ProviderResult
from .recovery import FailureState


def software_result_to_observation(result: ProviderResult) -> ExecutionObservation:
    """Keep computed results in details, never infer physical WorldState facts.

    No provider cost is reported. Zero is only the existing accumulator's
    placeholder, not a measured cost. Failures are terminal; this bridge does
    not choose retries or recovery actions.
    """
    return ExecutionObservation(
        action_success=result.action_success,
        failure=None if result.action_success else FailureState(result.failure_code),
        retryable=False,
        terminal_failure=not result.action_success,
        details={
            "provider_observations": result.observations,
            "provider_metrics": result.metrics,
            "provider_provenance": asdict(result.provenance) if result.provenance else None,
            "execution_cost": "NOT_VERIFIED",
            "cost_semantics": "UNKNOWN",
            "cost_unit": "UNKNOWN",
            "physical_state_updates": "NOT_VERIFIED",
        },
    )

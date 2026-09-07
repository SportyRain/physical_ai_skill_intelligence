"""Pure software-result bridge into the existing offline evaluation harness."""
from dataclasses import asdict

from .bounded_loop import ExecutionObservation
from .cost import OBSERVED_COST
from .provider_contract import ProviderResult
from .recovery import FailureState


def software_result_to_observation(result: ProviderResult) -> ExecutionObservation:
    """Keep computed results in details, never infer physical WorldState facts.

    UNKNOWN failures stop the offline harness without asserting terminal provider
    semantics. Known semantics require explicit provider evidence, not code maps.
    Unobserved cost retains only the legacy offline accumulator placeholder;
    provider_cost.value remains None for UNKNOWN. Use ProviderCost's observed
    experience gate for cost persistence; this bridge stores no experience.
    """
    return ExecutionObservation(
        action_success=result.action_success,
        failure=None if result.action_success else FailureState(result.failure_code),
        retryable=not result.action_success and result.failure_retryability == "retryable",
        terminal_failure=not result.action_success and result.failure_retryability == "terminal",
        cost=result.cost.value if result.cost.semantics == OBSERVED_COST else 0.0,
        details={
            "provider_observations": result.observations,
            "provider_metrics": result.metrics,
            "provider_provenance": asdict(result.provenance) if result.provenance else None,
            "failure_retryability": result.failure_retryability,
            "failure_semantics_reference": result.failure_semantics_reference,
            "provider_cost": asdict(result.cost),
            "execution_cost": result.cost.value if result.cost.semantics == OBSERVED_COST else "NOT_VERIFIED",
            "cost_semantics": result.cost.semantics,
            "cost_unit": result.cost.unit,
            "runtime_contract": asdict(result.runtime_contract),
            "runtime_result": asdict(result.runtime_result),
            "physical_state_updates": "NOT_VERIFIED",
        },
    )

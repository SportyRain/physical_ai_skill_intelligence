# Architecture

## Boundary

```text
                  physical_ai_skill_intelligence
                    (active AI development)
                               |
         +---------------------+---------------------+
         |                     |                     |
       Goal                World State           Experience
         |                     |                     |
         +---------------------+---------------------+
                               |
                       Outcome Estimator
                               |
                         Skill Ranking
                               |
                           Decision
                               |
                         Provider API
                               |
       +-----------------------+-----------------------+
       |                       |                       |
ur3_visual_servoing   ur3_vision_manipulation   peg-in-hole provider
       |                       |                       |
       +-----------------------+-----------------------+
                               |
                              UR3
```

Provider implementations remain outside this repository.

## Design constraints

1. No low-level robot control implementation.
2. No hidden wildcard generalization of unknown state.
3. Raw evidence provenance must remain traceable.
4. Action success must not be equated with goal success.
5. Decision logic must be deterministic for identical inputs in the baseline.
6. Unverified claims remain NOT_VERIFIED / UNKNOWN / UNRESOLVED / HYPOTHESIS.

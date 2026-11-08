"""CPU-only audit entry point; shared data logic lives in the study package."""

from self_model_study.confidence_data import (  # noqa: F401
    SPEC,
    all_inputs,
    audit,
    audit_tables,
    build_items,
    digest,
    main,
    normalized,
    prompt_for,
    selected_indices,
    token_audit,
    verified_sources,
)

if __name__ == "__main__":
    main()

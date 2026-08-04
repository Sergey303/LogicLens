"""Deterministic candidate and review data for the source pipeline contract."""

from __future__ import annotations

from typing import Any


def candidate(fragment_id: str) -> dict[str, Any]:
    """Build two typed assertions grounded in one source fragment."""
    return {
        "schemaVersion": "0.1",
        "proposalId": "internal-learning-model-v0",
        "sourceId": "internal-learning-model",
        "provider": {"kind": "fixture", "name": "contract-test"},
        "assertions": [
            {
                "assertionId": "rb.tl.contributes.direction",
                "target": {
                    "predicate": "contributes_to",
                    "arguments": ["role.team_lead", "outcome.technical_direction"],
                },
                "stance": "support",
                "grounding": [fragment_id],
                "dependencyGroup": "internal.learning_model.roles",
                "generalisability": "context-dependent",
            },
            {
                "assertionId": "rb.em.contributes.people",
                "target": {
                    "predicate": "contributes_to",
                    "arguments": [
                        "role.engineering_manager",
                        "outcome.people_development",
                    ],
                },
                "stance": "support",
                "grounding": [fragment_id],
                "dependencyGroup": "internal.learning_model.roles",
                "generalisability": "context-dependent",
            },
        ],
        "abstentions": [],
    }


def review(fragment_id: str) -> dict[str, Any]:
    """Build deterministic grounding decisions for the candidate assertions."""
    return {
        "schemaVersion": "0.1",
        "reviewId": "review-001",
        "proposalId": "internal-learning-model-v0",
        "reviewer": {"kind": "agent", "id": "contract-test"},
        "decisions": [
            {
                "assertionId": "rb.tl.contributes.direction",
                "decision": "accept",
                "grounding": "paraphrase",
                "evidenceQuotes": [
                    {
                        "fragmentId": fragment_id,
                        "quote": "Team Lead задаёт локальное техническое направление",
                    }
                ],
                "note": "The source directly names the role and technical direction.",
            },
            {
                "assertionId": "rb.em.contributes.people",
                "decision": "accept",
                "grounding": "direct",
                "evidenceQuotes": [
                    {
                        "fragmentId": fragment_id,
                        "quote": "Engineering Manager отвечает за развитие сотрудников",
                    }
                ],
                "note": "The source explicitly names people development.",
            },
        ],
    }

"""
Deterministic rules engine for Transaction Control.

Rules are defined as data (dataclasses) in a registry list.
The engine evaluates triggers and creates follow-up tasks
with idempotent dedupe keys to prevent duplicates on re-runs.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from tc.db.models.task import Task

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rule data structure
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RuleDef:
    """A single declarative rule: 'if *trigger* fires, create a task'."""

    trigger: str
    task_title_template: str
    task_category: str
    task_severity: str
    assign_to_coordinator: bool = False


# ---------------------------------------------------------------------------
# Rule registry — all business rules defined as data
# ---------------------------------------------------------------------------
RULES: list[RuleDef] = [
    RuleDef(
        trigger="task.due_soon",
        task_title_template="Reminder: Confirm '{task_title}' is scheduled",
        task_category="reminder",
        task_severity="medium",
    ),
    RuleDef(
        trigger="task.overdue",
        task_title_template="ESCALATION: '{task_title}' is overdue",
        task_category="escalation",
        task_severity="critical",
        assign_to_coordinator=True,
    ),
    RuleDef(
        trigger="appraisal.flagged_low",
        task_title_template="Negotiate: appraisal flagged low for '{task_title}'",
        task_category="negotiation",
        task_severity="high",
    ),
]


# ---------------------------------------------------------------------------
# Dedupe key builder
# ---------------------------------------------------------------------------
def build_dedupe_key(trigger: str, source_task_id: uuid.UUID) -> str:
    """Deterministic key so re-runs never create duplicate tasks."""
    return f"rule:{trigger}:{source_task_id}"


# ---------------------------------------------------------------------------
# Core evaluation function
# ---------------------------------------------------------------------------
def evaluate_rules(
    db: Session,
    *,
    trigger: str,
    source_task: Task,
) -> list[Task]:
    """
    Run every rule whose trigger matches, creating follow-up tasks.

    Returns the list of newly created tasks (empty if all deduplicated).
    """
    from tc.services.task_service import create_task

    matching_rules = [r for r in RULES if r.trigger == trigger]
    created: list[Task] = []

    for rule in matching_rules:
        dedupe_key = build_dedupe_key(trigger, source_task.id)

        # skip if a task with this key already exists
        exists = (
            db.query(Task.id)
            .filter(Task.dedupe_key == dedupe_key)
            .first()
        )
        if exists:
            logger.debug("Rule '%s' skipped — dedupe key '%s' exists", rule.trigger, dedupe_key)
            continue

        title = rule.task_title_template.format(task_title=source_task.title)

        new_task = create_task(
            db,
            transaction_id=source_task.transaction_id,
            title=title,
            dedupe_key=dedupe_key,
            category=rule.task_category,
            severity=rule.task_severity,
        )

        logger.info(
            "Rule '%s' created task %s (dedupe=%s)",
            rule.trigger,
            new_task.id,
            dedupe_key,
        )
        created.append(new_task)

    return created

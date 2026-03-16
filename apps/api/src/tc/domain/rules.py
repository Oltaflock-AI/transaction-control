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

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tc.db.models.task import Task

logger = logging.getLogger(__name__)

# Task.title column limit (String(255))
TASK_TITLE_MAX_LEN = 255


@dataclass(frozen=True)
class RuleDef:
    """A single declarative rule: 'if *trigger* fires, create a task'."""

    name: str
    trigger: str
    task_title_template: str
    task_category: str
    task_severity: str
    assign_to_coordinator: bool = False


RULES: list[RuleDef] = [
    RuleDef(
        name="due_soon_reminder",
        trigger="task.due_soon",
        task_title_template="Reminder: Confirm '{task_title}' is scheduled",
        task_category="reminder",
        task_severity="medium",
    ),
    RuleDef(
        name="overdue_escalation",
        trigger="task.overdue",
        task_title_template="ESCALATION: '{task_title}' is overdue",
        task_category="escalation",
        task_severity="critical",
        assign_to_coordinator=True,
    ),
    RuleDef(
        name="appraisal_low_negotiation",
        trigger="appraisal.flagged_low",
        task_title_template="Negotiate: appraisal flagged low for '{task_title}'",
        task_category="negotiation",
        task_severity="high",
    ),
]


def build_dedupe_key(rule_name: str, trigger: str, source_task_id: uuid.UUID) -> str:
    """Deterministic key so re-runs never create duplicate tasks."""
    return f"rule:{rule_name}:{trigger}:{source_task_id}"


def _is_dedupe_key_violation(exc: IntegrityError) -> bool:
    """True if the IntegrityError is a unique violation on the task dedupe_key constraint."""
    orig = getattr(exc, "orig", None)
    if orig is None:
        return False
    if getattr(orig, "pgcode", None) != "23505":
        return False
    constraint_name = getattr(getattr(orig, "diag", None), "constraint_name", None) or ""
    return "dedupe_key" in constraint_name


def _resolve_coordinator(db: Session, transaction_id: uuid.UUID) -> uuid.UUID | None:
    """Find the first admin member of the transaction's org to act as coordinator."""
    from tc.db.models.membership import Membership
    from tc.db.models.transaction import Transaction

    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if txn is None:
        return None
    membership = (
        db.query(Membership)
        .filter(Membership.org_id == txn.org_id, Membership.role == "admin")
        .order_by(Membership.user_id.asc())
        .first()
    )
    return membership.user_id if membership else None


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
        dedupe_key = build_dedupe_key(rule.name, trigger, source_task.id)

        exists = db.query(Task.id).filter(Task.dedupe_key == dedupe_key).first()
        if exists:
            logger.debug("Rule '%s' skipped — dedupe key '%s' exists", rule.name, dedupe_key)
            continue

        title = rule.task_title_template.format(task_title=source_task.title)
        if len(title) > TASK_TITLE_MAX_LEN:
            title = title[:TASK_TITLE_MAX_LEN]

        assignee_id = None
        if rule.assign_to_coordinator:
            assignee_id = _resolve_coordinator(db, source_task.transaction_id)

        try:
            with db.begin_nested():
                new_task = create_task(
                    db,
                    transaction_id=source_task.transaction_id,
                    title=title,
                    assignee_id=assignee_id,
                    dedupe_key=dedupe_key,
                    category=rule.task_category,
                    severity=rule.task_severity,
                    commit=False,
                )
        except IntegrityError as e:
            if _is_dedupe_key_violation(e):
                logger.debug(
                    "Rule '%s' skipped — dedupe key '%s' was inserted concurrently",
                    rule.name,
                    dedupe_key,
                )
                continue
            raise

        logger.info(
            "Rule '%s' created task %s (dedupe=%s)",
            rule.name,
            new_task.id,
            dedupe_key,
        )
        created.append(new_task)

    return created

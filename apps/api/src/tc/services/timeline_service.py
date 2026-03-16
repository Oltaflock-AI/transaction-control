from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.db.models.timeline import TimelineItem
from tc.domain.enums import TaskStatus

# Load the timeline templates JSON file
TEMPLATE_FILE = Path(__file__).parent.parent / "core" / "timeline_templates.json"


def load_template(template_name: str) -> list[dict]:
    """
    Load a named timeline template from the package's templates JSON.
    
    Parameters:
    	template_name (str): Name of the template to load.
    
    Returns:
    	list[dict]: List of task configuration dictionaries for the requested template.
    
    Raises:
    	ValueError: If no template with the given name exists in the JSON file.
    """
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        templates = json.load(f)
    if template_name not in templates:
        raise ValueError(f"Unknown timeline template: {template_name}")
    return templates[template_name]


def generate_default_timeline(
    db: Session, transaction_id: uuid.UUID, template_name: str = "sample_deal"
) -> list[Task]:
    """
    Create starter Task records and matching TimelineItem records for a transaction from a named template.
    
    Loads the specified template and, for each template entry, creates a Task and a corresponding TimelineItem with a due date computed by adding the entry's `offset_days` to the current UTC time. All created records are added to the database session and committed.
    
    Parameters:
        transaction_id (uuid.UUID): The transaction to attach the generated tasks and timeline items to.
        template_name (str): The name of the timeline template to load (defaults to "sample_deal").
    
    Returns:
        list[Task]: The list of Task objects created and persisted for the transaction.
    """
    now = datetime.now(UTC)
    tasks: list[Task] = []

    template = load_template(template_name)

    for task_config in template:
        title = task_config["title"]
        offset_days = task_config["offset_days"]
        description = task_config.get("description", "")
        category = task_config.get("category", "")
        severity = task_config.get("severity", "medium")

        due = now + timedelta(days=offset_days)

        task = Task(
            transaction_id=transaction_id,
            title=title,
            offset_days=offset_days,
            category=category,
            severity=severity,
            description=description,
            status=TaskStatus.todo,
            due_at=due,
        )
        db.add(task)
        tasks.append(task)

        item = TimelineItem(
            transaction_id=transaction_id,
            label=title,
            description=description,
            due_at=due,
        )
        db.add(item)

    db.commit()
    return tasks


def get_timeline_items(db: Session, transaction_id: uuid.UUID) -> list[TimelineItem]:
    """
    Retrieve timeline items for a transaction ordered by due date then ID.
    
    Returns:
        list[TimelineItem]: TimelineItem objects for the given transaction_id, ordered by `due_at` ascending then `id` ascending.
    """
    return (
        db.query(TimelineItem)
        .filter(TimelineItem.transaction_id == transaction_id)
        .order_by(TimelineItem.due_at.asc(), TimelineItem.id.asc())
        .all()
    )


def mark_item_complete(db: Session, item_id: uuid.UUID) -> TimelineItem | None:
    """
    Mark a timeline item as completed.
    
    Sets the item's `completed_at` timestamp only if it is currently unset and returns the refreshed TimelineItem; returns `None` if no item exists with the given id. If the item was already completed, the returned object reflects its existing state.
    
    Returns:
        TimelineItem | None: The timeline item after the operation, or `None` if not found.
    """
    from sqlalchemy import update

    item = db.query(TimelineItem).filter(TimelineItem.id == item_id).first()
    if item is None:
        return None
    now = datetime.now(UTC)
    result = db.execute(
        update(TimelineItem)
        .where(
            TimelineItem.id == item_id,
            TimelineItem.completed_at.is_(None),
        )
        .values(completed_at=now)
    )
    if result.rowcount == 0:
        db.refresh(item)
        return item
    db.commit()
    db.refresh(item)
    return item

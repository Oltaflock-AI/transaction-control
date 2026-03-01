from __future__ import annotations

import uuid
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from tc.db.models.task import Task
from tc.db.models.timeline import TimelineItem
from tc.domain.enums import TaskStatus

# Load the timeline templates JSON file
TEMPLATE_FILE = Path(__file__).parent.parent / "core" / "timeline_templates.json"

def load_template(template_name: str) -> list[dict]:
    """Load a timeline template by name from the JSON file."""
    with open(TEMPLATE_FILE, "r") as f:
        templates = json.load(f)
    return templates.get(template_name, [])


def generate_default_timeline(db: Session, transaction_id: uuid.UUID, template_name: str = "sample_deal") -> list[Task]:
    """Create a set of starter tasks and matching timeline items for a new transaction."""
    now = datetime.now(UTC)
    tasks: list[Task] = []

    template = load_template(template_name)

    for task_config in template:
        title = task_config["title"]
        offset_days = task_config["offset_days"]
        description = task_config.get("description", "")
        category = task_config.get("category", "")

        due = now + timedelta(days=offset_days)

        task = Task(
            transaction_id=transaction_id,
            title=title,
            offset_days=offset_days,
            category=category,
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
    return db.query(TimelineItem).filter(TimelineItem.transaction_id == transaction_id).all()

def mark_item_complete(db: Session, item_id: uuid.UUID) -> TimelineItem | None:
    item = db.query(TimelineItem).filter(TimelineItem.id == item_id).first()
    if item:
        item.completed_at = datetime.now(UTC)
        db.commit()
        db.refresh(item)
    return item
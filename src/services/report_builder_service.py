"""Custom report builder service."""
from datetime import datetime, date
from typing import Any, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from io import StringIO, BytesIO
import csv

from src.models import Member, Student, Grant
from src.models.dues_payment import DuesPayment


class ReportBuilderService:
    """Service for building custom reports."""

    AVAILABLE_ENTITIES = {
        "members": {
            "model": Member,
            "fields": [
                "id",
                "member_number",
                "first_name",
                "last_name",
                "email",
                "status",
                "classification",
                "created_at",
            ],
            "label": "Members",
        },
        "students": {
            "model": Student,
            "fields": [
                "id",
                "first_name",
                "last_name",
                "email",
                "status",
                "cohort_id",
                "created_at",
            ],
            "label": "Students",
        },
        "payments": {
            "model": DuesPayment,
            "fields": [
                "id",
                "member_id",
                "amount_due",
                "amount_paid",
                "payment_date",
                "payment_method",
                "status",
            ],
            "label": "Dues Payments",
        },
        "grants": {
            "model": Grant,
            "fields": [
                "id",
                "name",
                "funding_source",
                "total_amount",
                "status",
                "start_date",
                "end_date",
            ],
            "label": "Grants",
        },
    }

    def __init__(self, db: Session):
        self.db = db

    def get_available_entities(self) -> list[dict]:
        """Get list of entities available for reporting."""
        return [
            {"key": key, "label": config["label"], "fields": config["fields"]}
            for key, config in self.AVAILABLE_ENTITIES.items()
        ]

    def build_report(
        self,
        entity: str,
        fields: list[str],
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        limit: int = 1000,
    ) -> dict:
        """Build a custom report based on parameters."""
        if entity not in self.AVAILABLE_ENTITIES:
            raise ValueError(f"Unknown entity: {entity}")

        config = self.AVAILABLE_ENTITIES[entity]
        model = config["model"]

        # Validate fields
        valid_fields = [f for f in fields if f in config["fields"]]
        if not valid_fields:
            valid_fields = config["fields"][:5]  # Default to first 5 fields

        # Build query
        columns = [getattr(model, f) for f in valid_fields if hasattr(model, f)]
        query = select(*columns)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    column = getattr(model, field)
                    if isinstance(value, dict):
                        if "gte" in value:
                            query = query.where(column >= value["gte"])
                        if "lte" in value:
                            query = query.where(column <= value["lte"])
                        if "eq" in value:
                            query = query.where(column == value["eq"])
                    else:
                        query = query.where(column == value)

        # Apply ordering
        if order_by and hasattr(model, order_by.lstrip("-")):
            order_field = order_by.lstrip("-")
            order_col = getattr(model, order_field)
            if order_by.startswith("-"):
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())

        # Apply limit
        query = query.limit(limit)

        # Execute
        result = self.db.execute(query)
        rows = result.fetchall()

        # Format results
        data = []
        for row in rows:
            row_dict = {}
            for i, field in enumerate(valid_fields):
                if i < len(row):
                    value = row[i]
                    # Serialize dates and enums
                    if isinstance(value, (datetime, date)):
                        value = value.isoformat()
                    elif hasattr(value, "value"):  # Enum
                        value = value.value
                    row_dict[field] = value
            data.append(row_dict)

        return {
            "entity": entity,
            "fields": valid_fields,
            "filters": filters,
            "count": len(data),
            "data": data,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def export_to_csv(self, report: dict) -> str:
        """Convert report to CSV format."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=report["fields"])
        writer.writeheader()
        writer.writerows(report["data"])
        return output.getvalue()

    def export_to_excel(self, report: dict) -> bytes:
        """Convert report to Excel format."""
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = report["entity"].title()

        # Header row
        ws.append(report["fields"])

        # Data rows
        for row in report["data"]:
            ws.append([row.get(f) for f in report["fields"]])

        # Style header
        for cell in ws[1]:
            cell.font = Font(bold=True)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output.getvalue()

from datetime import datetime
from uuid import uuid4
from models.observability_records import ReleaseValidationRecord
from .audit import record_audit


def record_release_validation(store, *, report, release_target_id: str, created_at: datetime) -> ReleaseValidationRecord:
    passed = tuple(item.check_id for item in report.checks if item.passed)
    failed = tuple(item.check_id for item in report.checks if not item.passed)
    record = ReleaseValidationRecord(
        validation_record_id=f"RELVAL_{uuid4().hex}",
        project_id=report.project_id,
        release_id=report.release_id,
        release_target_id=release_target_id,
        target_type=report.target_type,
        ready=report.ready,
        passed_check_ids=passed,
        failed_check_ids=failed,
        created_at=created_at,
    )
    store.append_release_validation_record(record)
    record_audit(
        store,
        project_id=record.project_id,
        category="RELEASE",
        event_type="RELEASE_VALIDATION",
        occurred_at=created_at,
        resource_type="ReleaseTarget",
        resource_id=release_target_id,
        correlation_id=record.release_id,
        severity="INFO" if record.ready else "WARNING",
        details={"ready": record.ready, "failed_check_ids": list(record.failed_check_ids)},
    )
    return record

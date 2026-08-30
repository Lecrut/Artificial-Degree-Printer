"""
Unit test suite for CoreProcessingService.
"""
import pytest
from src.core.service import CoreProcessingService

def test_service_initialization():
    service = CoreProcessingService("TestService")
    assert service.service_name == "TestService"

def test_submit_and_execute_task():
    service = CoreProcessingService()
    task = service.submit_task("T-1", {"items": [1, 2, 3, 4]})
    assert task.status == "pending"

    res = service.execute_task("T-1")
    assert res["status"] == "completed"
    assert res["processed_items"] == 4
    assert service.get_task("T-1").status == "completed"

def test_duplicate_task_rejection():
    service = CoreProcessingService()
    service.submit_task("T-2", {})
    with pytest.raises(ValueError):
        service.submit_task("T-2", {})

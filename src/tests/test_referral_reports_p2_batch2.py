"""
Tests for Week 41 P2 Batch 2 Reports - Dispatch, Employer & Enforcement Analytics.

Created: February 6, 2026
Phase 7g - Report Implementation
"""

import pytest
from uuid import uuid4
from src.services.referral_report_service import ReferralReportService


# Note: Using fixtures from conftest.py and test_referral_reports_p2_batch1.py


# --- Theme A: Dispatch Operations (12 tests) ---


def test_dispatch_success_rate_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_dispatch_success_rate_report(format="pdf")
    assert isinstance(result, bytes)


def test_dispatch_success_rate_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/dispatch-success-rate", headers=auth_headers)
    assert response.status_code == 200


def test_time_to_fill_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_time_to_fill_report(format="pdf")
    assert isinstance(result, bytes)


def test_time_to_fill_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/time-to-fill", headers=auth_headers)
    assert response.status_code == 200


def test_dispatch_method_comparison_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_dispatch_method_comparison_report(format="pdf")
    assert isinstance(result, bytes)


def test_dispatch_method_comparison_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/dispatch-method-comparison", headers=auth_headers)
    assert response.status_code == 200


def test_dispatch_geographic_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_dispatch_geographic_report(format="pdf")
    assert isinstance(result, bytes)


def test_dispatch_geographic_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/dispatch-geographic", headers=auth_headers)
    assert response.status_code == 200


def test_termination_reason_analysis_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_termination_reason_analysis_report(format="pdf")
    assert isinstance(result, bytes)


def test_termination_reason_analysis_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/termination-reason-analysis", headers=auth_headers)
    assert response.status_code == 200


def test_return_dispatch_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_return_dispatch_report(format="pdf")
    assert isinstance(result, bytes)


def test_return_dispatch_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/return-dispatch", headers=auth_headers)
    assert response.status_code == 200


# --- Theme B: Employer Intelligence (12 tests) ---


def test_employer_growth_trends_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_employer_growth_trends_report(format="pdf")
    assert isinstance(result, bytes)


def test_employer_growth_trends_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/employer-growth-trends", headers=auth_headers)
    assert response.status_code == 200


def test_employer_workforce_size_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_employer_workforce_size_report(format="pdf")
    assert isinstance(result, bytes)


def test_employer_workforce_size_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/employer-workforce-size", headers=auth_headers)
    assert response.status_code == 200


def test_new_employer_activity_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_new_employer_activity_report(format="pdf")
    assert isinstance(result, bytes)


def test_new_employer_activity_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/new-employer-activity", headers=auth_headers)
    assert response.status_code == 200


def test_contract_code_utilization_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_contract_code_utilization_report(format="pdf")
    assert isinstance(result, bytes)


def test_contract_code_utilization_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/contract-code-utilization", headers=auth_headers)
    assert response.status_code == 200


def test_queue_velocity_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_queue_velocity_report(format="pdf")
    assert isinstance(result, bytes)


def test_queue_velocity_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/queue-velocity", headers=auth_headers)
    assert response.status_code == 200


def test_peak_demand_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_peak_demand_report(format="pdf")
    assert isinstance(result, bytes)


def test_peak_demand_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/peak-demand", headers=auth_headers)
    assert response.status_code == 200


# --- Theme C: Enforcement (14 tests) ---


def test_check_mark_patterns_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_check_mark_patterns_report(format="pdf")
    assert isinstance(result, bytes)


def test_check_mark_patterns_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/check-mark-patterns", headers=auth_headers)
    assert response.status_code == 200


def test_check_mark_exceptions_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_check_mark_exceptions_report(format="pdf")
    assert isinstance(result, bytes)


def test_check_mark_exceptions_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/check-mark-exceptions", headers=auth_headers)
    assert response.status_code == 200


def test_internet_bidding_analytics_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_internet_bidding_analytics_report(format="pdf")
    assert isinstance(result, bytes)


def test_internet_bidding_analytics_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/internet-bidding-analytics", headers=auth_headers)
    assert response.status_code == 200


def test_exemption_status_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_exemption_status_report(format="pdf")
    assert isinstance(result, bytes)


def test_exemption_status_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/exemption-status", headers=auth_headers)
    assert response.status_code == 200


def test_agreement_type_performance_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_agreement_type_performance_report(format="pdf")
    assert isinstance(result, bytes)


def test_agreement_type_performance_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/agreement-type-performance", headers=auth_headers)
    assert response.status_code == 200


def test_foreperson_by_name_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_foreperson_by_name_report(format="pdf")
    assert isinstance(result, bytes)


def test_foreperson_by_name_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/foreperson-by-name", headers=auth_headers)
    assert response.status_code == 200


def test_blackout_period_tracking_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_blackout_period_tracking_report(format="pdf")
    assert isinstance(result, bytes)


def test_blackout_period_tracking_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/blackout-period-tracking", headers=auth_headers)
    assert response.status_code == 200

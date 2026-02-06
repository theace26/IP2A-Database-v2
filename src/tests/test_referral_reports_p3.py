"""
Tests for Week 42 P3 Reports - Projections, Intelligence & Admin.

Created: February 6, 2026
Phase 7g - Report Implementation
"""

import pytest
from src.services.referral_report_service import ReferralReportService


# --- P3-A: Forecasting (6 tests) ---

def test_workforce_projection_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_workforce_projection_report(format="pdf")
    assert isinstance(result, bytes)


def test_workforce_projection_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/workforce-projection", headers=auth_headers)
    assert response.status_code == 200


def test_dispatch_forecast_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_dispatch_forecast_report(format="pdf")
    assert isinstance(result, bytes)


def test_dispatch_forecast_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/dispatch-forecast", headers=auth_headers)
    assert response.status_code == 200


def test_book_demand_forecast_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_book_demand_forecast_report(format="pdf")
    assert isinstance(result, bytes)


def test_book_demand_forecast_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/book-demand-forecast", headers=auth_headers)
    assert response.status_code == 200


# --- P3-B: Intelligence (8 tests) ---

def test_member_availability_index_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_member_availability_index_report(format="pdf")
    assert isinstance(result, bytes)


def test_member_availability_index_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/member-availability-index", headers=auth_headers)
    assert response.status_code == 200


def test_employer_loyalty_score_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_employer_loyalty_score_report(format="pdf")
    assert isinstance(result, bytes)


def test_employer_loyalty_score_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/employer-loyalty-score", headers=auth_headers)
    assert response.status_code == 200


def test_member_journey_service(db_session, test_member_w40):
    service = ReferralReportService(db_session)
    result = service.generate_member_journey_report(format="pdf", member_id=test_member_w40.id)
    assert isinstance(result, bytes)


def test_member_journey_api(client, auth_headers, test_member_w40):
    response = client.get(f"/api/v1/reports/referral/member-journey?member_id={test_member_w40.id}", headers=auth_headers)
    assert response.status_code == 200


def test_comparative_book_performance_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_comparative_book_performance_report(format="pdf")
    assert isinstance(result, bytes)


def test_comparative_book_performance_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/comparative-book-performance", headers=auth_headers)
    assert response.status_code == 200


# --- P3-C: Administrative (6 tests) ---

def test_custom_export_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_custom_export_report(format="xlsx", entity_type="members")
    assert isinstance(result, bytes)


def test_custom_export_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/custom-export?entity_type=members", headers=auth_headers)
    assert response.status_code == 200


def test_annual_summary_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_annual_summary_report(format="pdf")
    assert isinstance(result, bytes)


def test_annual_summary_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/annual-summary", headers=auth_headers)
    assert response.status_code == 200


def test_data_quality_service(db_session):
    service = ReferralReportService(db_session)
    result = service.generate_data_quality_report(format="pdf")
    assert isinstance(result, bytes)


def test_data_quality_api(client, auth_headers):
    response = client.get("/api/v1/reports/referral/data-quality", headers=auth_headers)
    assert response.status_code == 200

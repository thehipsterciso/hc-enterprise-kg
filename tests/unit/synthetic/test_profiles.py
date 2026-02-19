"""Tests for organization profiles."""

from hc_enterprise_kg.synthetic.profiles.financial_org import financial_org
from hc_enterprise_kg.synthetic.profiles.healthcare_org import healthcare_org
from hc_enterprise_kg.synthetic.profiles.tech_company import mid_size_tech_company


class TestProfiles:
    def test_tech_profile(self):
        profile = mid_size_tech_company(500)
        assert profile.employee_count == 500
        assert profile.industry == "technology"
        assert len(profile.department_specs) == 10
        fractions = sum(s.headcount_fraction for s in profile.department_specs)
        assert 0.99 <= fractions <= 1.01

    def test_healthcare_profile(self):
        profile = healthcare_org(2000)
        assert profile.employee_count == 2000
        assert profile.industry == "healthcare"
        assert len(profile.department_specs) == 10

    def test_financial_profile(self):
        profile = financial_org(1000)
        assert profile.employee_count == 1000
        assert profile.industry == "financial_services"
        assert len(profile.department_specs) == 11

    def test_profile_custom_employee_count(self):
        profile = mid_size_tech_company(100)
        assert profile.employee_count == 100

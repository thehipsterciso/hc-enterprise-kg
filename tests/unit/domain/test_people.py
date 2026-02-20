"""Tests for L05: People & Roles entity types.

Covers Person (extended) and Role (extended) entities with full attribute
group coverage, sub-model instantiation, backward compatibility, and
JSON serialization roundtrip.
"""

from pydantic import TypeAdapter

from domain.base import EntityType
from domain.entities import AnyEntity
from domain.entities.person import (
    AccessPrivilege,
    AcquisitionOrigin,
    BackgroundCheckStatus,
    CareerAspirations,
    CertificationHeld,
    ClearanceHeld,
    ConflictOfInterestDeclaration,
    CurrentRoleAssignment,
    DevelopmentPlan,
    Education,
    ExperienceProfile,
    InsiderStatus,
    LanguageProficiency,
    MandatoryTrainingCompliance,
    PerformanceRating,
    Person,
    PersonDottedLine,
    PersonName,
    PotentialAssessment,
    RegulatoryFitness,
    ReportingRelationship,
    RetentionAction,
    SkillInventoryItem,
    SkillsGapAssessment,
    SuccessionCandidacy,
    TrainingCompleted,
    UnitMembership,
)
from domain.entities.role import (
    AuthorityDelegated,
    CapabilityContribution,
    CompensationRange,
    CompetencyModelReference,
    CompetencyReference,
    ContractAuthority,
    DataAccessRequirement,
    DecisionRight,
    DirectReportsTarget,
    DottedLineRelationship,
    FinancialLimit,
    GovernanceMembership,
    HeadcountByLocation,
    LanguageRequirement,
    PhysicalRequirements,
    RegulatoryAccountability,
    RequiredCertification,
    RequiredClearance,
    RequiredEducation,
    RequiredExperience,
    RequiredSkill,
    Role,
    RoleFamily,
    RoleFormerName,
    RoleLevel,
    RoleLocalName,
    RoleMandateDocument,
    RoleTaxonomyLineage,
    SystemAccessRequirement,
    TravelRequirement,
    UnitAssignment,
    VacancyDuration,
)

_any_entity_adapter = TypeAdapter(AnyEntity)


# ===========================================================================
# Role tests
# ===========================================================================


class TestRoleExtended:
    def test_minimal_construction(self):
        role = Role(name="CISO")
        assert role.entity_type == EntityType.ROLE
        assert role.name == "CISO"
        assert role.department_id is None  # v0.1 field
        assert role.role_id == ""

    def test_backward_compat_v01_fields(self):
        role = Role(
            name="Security Analyst",
            department_id="dept-001",
            access_level="elevated",
            is_privileged=True,
            permissions=["read", "write", "admin"],
            max_headcount=5,
        )
        assert role.department_id == "dept-001"
        assert role.access_level == "elevated"
        assert role.is_privileged is True
        assert role.permissions == ["read", "write", "admin"]
        assert role.max_headcount == 5

    def test_identity_classification(self):
        role = Role(
            name="Chief Information Security Officer",
            role_id="RL-00001",
            role_type="Executive",
            role_subtype="C-Suite Security",
            functional_domain_primary="Risk & Compliance",
            functional_domain_secondary=["Technology & Digital"],
            role_family=RoleFamily(
                family_name="Information Security", subfamily="Executive Leadership"
            ),
            role_level=RoleLevel(
                level_code="E1",
                level_name="C-Suite",
                level_band="Executive Band",
            ),
            origin="Organic",
            regulatory_designation="Regulatory Required",
            role_name_local=[RoleLocalName(language_code="de", name="CISO", locale="DE")],
            role_name_former=[
                RoleFormerName(
                    former_name="VP Security",
                    from_date="2018-01-01",
                    to_date="2022-06-30",
                    change_reason="Title upgrade",
                )
            ],
            taxonomy_lineage=[
                RoleTaxonomyLineage(
                    framework="NICE Workforce Framework",
                    framework_element_id="OV-MGT-001",
                    mapping_confidence="Strong Analog",
                )
            ],
        )
        assert role.role_id == "RL-00001"
        assert role.role_family.family_name == "Information Security"
        assert role.role_level.level_band == "Executive Band"
        assert len(role.taxonomy_lineage) == 1

    def test_requirements_competencies(self):
        role = Role(
            name="Data Engineer",
            required_skills=[
                RequiredSkill(
                    skill_id="SK-001",
                    skill_name="SQL",
                    skill_category="Technical",
                    proficiency_level_required="Expert",
                    criticality="Must Have",
                ),
            ],
            required_certifications=[
                RequiredCertification(
                    certification_name="AWS Solutions Architect",
                    issuing_body="Amazon Web Services",
                    requirement_level="Strongly Preferred",
                )
            ],
            required_experience=RequiredExperience(
                minimum_years_total=5,
                minimum_years_in_domain=3,
                international_experience_required=False,
            ),
            required_education=RequiredEducation(
                minimum_level="Bachelor",
                preferred_fields=["Computer Science", "Data Engineering"],
            ),
            required_clearances=[
                RequiredClearance(clearance_type="Secret", jurisdiction="US", mandatory=True)
            ],
            competency_model_reference=CompetencyModelReference(
                model_name="Enterprise Tech Competencies",
                applicable_competencies=[
                    CompetencyReference(competency_name="Data Modeling", required_level="Expert")
                ],
            ),
            language_requirements=[
                LanguageRequirement(
                    language="en",
                    proficiency_level="Full Professional",
                    requirement_level="Mandatory",
                )
            ],
            travel_requirement=TravelRequirement(travel_pct=10, travel_scope="National"),
            physical_requirements=PhysicalRequirements(
                has_physical_requirements=False, work_environment="Office Only"
            ),
            authority_delegated=AuthorityDelegated(
                financial_approval_limit=FinancialLimit(amount=50000, currency="USD"),
                hiring_authority="Individual Contributors Only",
                contract_authority=ContractAuthority(max_value=25000, max_term_months=12),
                system_access_level="Power User",
                data_access_level="Department Scope",
            ),
        )
        assert len(role.required_skills) == 1
        assert role.required_skills[0].proficiency_level_required == "Expert"
        assert role.required_experience.minimum_years_total == 5
        assert role.authority_delegated.financial_approval_limit.amount == 50000

    def test_governance_accountability(self):
        role = Role(
            name="VP Engineering",
            reports_to_role="RL-CTO",
            dotted_line_to=[
                DottedLineRelationship(
                    role_id="RL-CISO",
                    relationship_type="Governance Oversight",
                    influence_strength="Moderate",
                )
            ],
            direct_reports_target=DirectReportsTarget(
                target_count=8, actual_count=7, includes_roles=["RL-EM", "RL-SRE"]
            ),
            governance_memberships=[
                GovernanceMembership(
                    governance_body_name="Technology Council",
                    membership_type="Voting Member",
                    cadence="Monthly",
                )
            ],
            decision_rights=[
                DecisionRight(
                    decision_type="Architecture Decisions",
                    authority_level="Decide",
                    scope="Engineering Division",
                )
            ],
            regulatory_accountability=[
                RegulatoryAccountability(
                    regulation="SOX Section 404",
                    accountability_description="IT controls owner",
                    personal_liability_flag=False,
                    jurisdiction="US",
                )
            ],
            succession_criticality="Critical — Must Have Successor",
            role_mandate_document=RoleMandateDocument(
                document_reference="DOC-VP-ENG-2024",
                document_date="2024-01-15",
            ),
        )
        assert role.reports_to_role == "RL-CTO"
        assert role.succession_criticality == "Critical — Must Have Successor"
        assert len(role.governance_memberships) == 1

    def test_capacity_allocation(self):
        role = Role(
            name="Software Engineer",
            headcount_authorized=50,
            headcount_filled=42,
            headcount_vacant=8,
            vacancy_duration=VacancyDuration(
                average_days_vacant=45,
                longest_vacancy_days=120,
                active_recruitment=True,
                recruitment_stage="Interviewing",
            ),
            headcount_by_location=[
                HeadcountByLocation(
                    location_id="LOC-NYC",
                    location_name="New York",
                    authorized=30,
                    filled=25,
                    vacant=5,
                )
            ],
            allocation_model="Dedicated to Single Unit",
            location_flexibility="Hybrid — Primarily Remote",
            employment_type_target="Full-Time Employee",
            compensation_range=CompensationRange(
                minimum=120000,
                midpoint=160000,
                maximum=200000,
                currency="USD",
                compensation_type="Total Cash Compensation",
                benchmark_source="Radford",
                benchmark_percentile_target=75,
            ),
        )
        assert role.headcount_authorized == 50
        assert role.headcount_vacant == 8
        assert role.vacancy_duration.recruitment_stage == "Interviewing"
        assert role.compensation_range.midpoint == 160000

    def test_edge_interface_ports(self):
        role = Role(
            name="Security Architect",
            fills_capability=[
                CapabilityContribution(capability_id="CAP-SEC", contribution_type="Accountable")
            ],
            belongs_to_unit=[UnitAssignment(unit_id="OU-SEC", assignment_type="Primary")],
            filled_by_persons=["PS-001", "PS-002"],
            requires_systems_access=[
                SystemAccessRequirement(system_id="SYS-SIEM", access_level="Admin")
            ],
            requires_data_access=[
                DataAccessRequirement(data_asset_id="DA-LOGS", access_type="Read")
            ],
            governed_by=["REG-SOX"],
            supports_initiatives=["INIT-ZT"],
        )
        assert len(role.fills_capability) == 1
        assert len(role.filled_by_persons) == 2
        assert role.requires_systems_access[0].access_level == "Admin"

    def test_json_roundtrip(self):
        role = Role(
            name="Data Steward",
            role_id="RL-12345",
            role_type="Professional / Individual Contributor",
            functional_domain_primary="Data & Analytics",
            required_skills=[
                RequiredSkill(
                    skill_id="SK-DQ",
                    skill_name="Data Quality",
                    skill_category="Domain / Subject Matter",
                    proficiency_level_required="Expert",
                    criticality="Must Have",
                )
            ],
            headcount_authorized=3,
            headcount_filled=2,
            headcount_vacant=1,
        )
        data = role.model_dump(mode="json")
        restored = Role.model_validate(data)
        assert restored.role_id == "RL-12345"
        assert restored.required_skills[0].skill_name == "Data Quality"
        assert restored.headcount_vacant == 1

    def test_any_entity_roundtrip(self):
        role = Role(
            name="Compliance Officer",
            role_id="RL-CO-001",
            role_type="Professional / Individual Contributor",
        )
        data = role.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Role)
        assert restored.role_id == "RL-CO-001"


# ===========================================================================
# Person tests
# ===========================================================================


class TestPersonExtended:
    def test_minimal_construction(self):
        person = Person(
            name="Jane Doe",
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
        )
        assert person.entity_type == EntityType.PERSON
        assert person.first_name == "Jane"
        assert person.person_id == ""

    def test_backward_compat_v01_fields(self):
        person = Person(
            name="John Smith",
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            title="Senior Engineer",
            employee_id="EMP-001",
            clearance_level="Secret",
            is_active=True,
            hire_date="2020-03-15",
            phone="+1-555-1234",
            department_id="dept-eng",
        )
        assert person.title == "Senior Engineer"
        assert person.clearance_level == "Secret"
        assert person.hire_date == "2020-03-15"
        assert person.department_id == "dept-eng"

    def test_identity_group(self):
        person = Person(
            name="Maria Garcia",
            first_name="Maria",
            last_name="Garcia",
            email="m.garcia@example.com",
            person_id="PS-00001",
            person_name=PersonName(
                display_name="Maria Garcia",
                given_name="Maria",
                family_name="Garcia",
                preferred_name="Mari",
            ),
            employment_status="Active",
            employment_type="Full-Time",
            original_hire_date="2015-06-01",
            acquisition_origin=AcquisitionOrigin(
                acquisition_name="TechCorp Acquisition",
                acquisition_date="2019-03-01",
                pre_acquisition_tenure_years=4.0,
                pre_acquisition_role="Staff Engineer",
            ),
            location_primary="LOC-NYC",
            location_secondary=["LOC-SF"],
        )
        assert person.person_id == "PS-00001"
        assert person.person_name.preferred_name == "Mari"
        assert person.acquisition_origin.pre_acquisition_tenure_years == 4.0
        assert person.location_primary == "LOC-NYC"

    def test_current_assignment(self):
        person = Person(
            name="Alex Chen",
            first_name="Alex",
            last_name="Chen",
            email="a.chen@example.com",
            current_roles=[
                CurrentRoleAssignment(
                    role_id="RL-SWE",
                    assignment_type="Primary",
                    allocation_pct=80,
                    start_date="2023-01-15",
                ),
                CurrentRoleAssignment(
                    role_id="RL-TL",
                    assignment_type="Acting",
                    allocation_pct=20,
                    start_date="2024-06-01",
                    expected_end_date="2024-12-31",
                ),
            ],
            organizational_unit_primary="OU-ENG",
            organizational_unit_secondary=["OU-PLATFORM"],
            reporting_to=ReportingRelationship(
                manager_person_id="PS-MGR",
                manager_role_id="RL-EM",
                reporting_type="Solid Line",
            ),
            dotted_line_to=[
                PersonDottedLine(
                    person_id="PS-ARCH",
                    role_id="RL-ARCH",
                    relationship_type="Technical",
                )
            ],
            cost_center="CC-ENG-001",
            work_arrangement="Hybrid — Primarily Remote",
            timezone="America/New_York",
        )
        assert len(person.current_roles) == 2
        assert person.current_roles[0].allocation_pct == 80
        assert person.reporting_to.reporting_type == "Solid Line"
        assert person.timezone == "America/New_York"

    def test_skills_competencies(self):
        person = Person(
            name="Bob Wilson",
            first_name="Bob",
            last_name="Wilson",
            email="b.wilson@example.com",
            skills_inventory=[
                SkillInventoryItem(
                    skill_id="SK-PY",
                    skill_name="Python",
                    skill_category="Technical",
                    proficiency_level_actual="Expert",
                    proficiency_source="Certification Verified",
                    last_validated_date="2024-06-01",
                )
            ],
            certifications_held=[
                CertificationHeld(
                    certification_name="CISSP",
                    issuing_body="ISC2",
                    date_obtained="2022-01-15",
                    expiration_date="2025-01-15",
                    status="Active",
                    credential_id="CISSP-123456",
                )
            ],
            education=[
                Education(
                    institution="MIT",
                    degree_level="Master",
                    field_of_study="Computer Science",
                    graduation_year=2018,
                )
            ],
            clearances_held=[
                ClearanceHeld(
                    clearance_type="Top Secret",
                    jurisdiction="US",
                    status="Active",
                    expiration_date="2027-01-01",
                )
            ],
            languages=[
                LanguageProficiency(language="en", proficiency_level="Native / Bilingual"),
                LanguageProficiency(language="es", proficiency_level="Professional Working"),
            ],
            experience_profile=ExperienceProfile(
                total_years_professional=12,
                years_in_current_role=3,
                years_in_current_domain=8,
                years_at_enterprise=5,
            ),
            training_completed=[
                TrainingCompleted(
                    training_name="AWS Security Specialty",
                    training_category="Technical",
                    completion_date="2024-03-15",
                    provider="AWS",
                    hours=40,
                )
            ],
            skills_gap_assessment=[
                SkillsGapAssessment(
                    role_id="RL-ARCH",
                    skill_id="SK-K8S",
                    skill_name="Kubernetes",
                    required_level="Expert",
                    actual_level="Practitioner",
                    gap_severity="Significant Gap",
                )
            ],
        )
        assert len(person.skills_inventory) == 1
        assert person.certifications_held[0].status == "Active"
        assert person.experience_profile.total_years_professional == 12
        assert len(person.languages) == 2
        assert person.skills_gap_assessment[0].gap_severity == "Significant Gap"

    def test_performance_development(self):
        person = Person(
            name="Sarah Lee",
            first_name="Sarah",
            last_name="Lee",
            email="s.lee@example.com",
            performance_rating_current=PerformanceRating(
                rating="Exceeds Expectations",
                rating_scale="5-point",
                period="FY2024",
                rated_by="PS-MGR",
                calibrated=True,
            ),
            performance_rating_history=[
                PerformanceRating(
                    rating="Meets Expectations",
                    rating_scale="5-point",
                    period="FY2023",
                    rated_by="PS-MGR",
                )
            ],
            performance_trajectory="High Performer — Accelerating",
            potential_assessment=PotentialAssessment(
                potential_level="High Potential",
                assessment_methodology="Talent Review Panel",
                assessed_date="2024-09-01",
            ),
            development_plan=DevelopmentPlan(
                plan_reference="IDP-2024-SL",
                focus_areas=["Architecture", "Leadership"],
                target_role="RL-ARCH",
                target_role_name="Principal Architect",
                target_timeline="18 months",
                plan_status="Active",
            ),
            career_aspirations=CareerAspirations(
                target_role_family="Architecture",
                target_level="Principal",
                mobility_willingness="Open to Domestic Relocation",
                aspiration_timeline="2-3 years",
            ),
            flight_risk="Low",
            retention_actions=[
                RetentionAction(
                    action_description="Assigned to strategic project",
                    action_type="Development Opportunity",
                    action_date="2024-06-01",
                    status="Completed",
                )
            ],
        )
        assert person.performance_rating_current.rating == "Exceeds Expectations"
        assert person.performance_trajectory == "High Performer — Accelerating"
        assert person.potential_assessment.potential_level == "High Potential"
        assert person.development_plan.plan_status == "Active"
        assert person.flight_risk == "Low"

    def test_risk_compliance(self):
        person = Person(
            name="Tom Brown",
            first_name="Tom",
            last_name="Brown",
            email="t.brown@example.com",
            background_check_status=BackgroundCheckStatus(
                status="Completed — Clear",
                check_type=["Criminal", "Credit", "Education"],
                completion_date="2023-01-10",
                next_due_date="2026-01-10",
                provider="Sterling",
            ),
            conflict_of_interest_declarations=[
                ConflictOfInterestDeclaration(
                    declaration_type="Outside Employment",
                    description="Advisory board member at startup",
                    status="Declared — Approved",
                    review_date="2024-01-15",
                    reviewer="PS-ETHICS",
                )
            ],
            regulatory_fitness=[
                RegulatoryFitness(
                    regulation="SEC Rule 17a-4",
                    fitness_status="Fit and Proper — Confirmed",
                    assessment_date="2024-03-01",
                    next_assessment_date="2025-03-01",
                )
            ],
            access_privileges=[
                AccessPrivilege(
                    system_id="SYS-SAP",
                    system_name="SAP ERP",
                    access_level="Standard",
                    last_access_review_date="2024-06-01",
                    next_review_date="2024-12-01",
                    access_justified=True,
                )
            ],
            insider_status=InsiderStatus(
                is_insider=True,
                insider_type="Designated Insider",
                effective_date="2024-01-01",
                trading_restrictions="Quarterly blackout periods",
            ),
            mandatory_training_compliance=[
                MandatoryTrainingCompliance(
                    training_requirement="Anti-Money Laundering",
                    regulatory_basis="BSA/AML",
                    completion_status="Completed",
                    due_date="2024-06-30",
                    completion_date="2024-05-15",
                    overdue_flag=False,
                )
            ],
        )
        assert person.background_check_status.status == "Completed — Clear"
        assert person.insider_status.is_insider is True
        assert len(person.conflict_of_interest_declarations) == 1
        assert person.mandatory_training_compliance[0].completion_status == "Completed"

    def test_edge_interface_ports(self):
        person = Person(
            name="Lisa Wang",
            first_name="Lisa",
            last_name="Wang",
            email="l.wang@example.com",
            holds_roles=["RL-SWE", "RL-TL"],
            member_of_unit=[
                UnitMembership(unit_id="OU-ENG", membership_type="Primary"),
                UnitMembership(unit_id="OU-PLATFORM", membership_type="Matrix"),
            ],
            located_at=["LOC-NYC", "LOC-SF"],
            has_system_access=["SYS-JIRA", "SYS-GH"],
            manages_vendor_relationships=["VENDOR-AWS"],
            subject_to_compliance=["REG-SOX"],
            participates_in_initiatives=["INIT-CLOUD"],
            succession_candidate_for=[
                SuccessionCandidacy(
                    role_id="RL-DIR-ENG",
                    readiness="Ready in 1 Year",
                    development_gaps=["Budget management", "Cross-org influence"],
                )
            ],
            mentors=["PS-JR-001", "PS-JR-002"],
            mentored_by="PS-VP-ENG",
        )
        assert len(person.holds_roles) == 2
        assert len(person.member_of_unit) == 2
        assert person.succession_candidate_for[0].readiness == "Ready in 1 Year"
        assert person.mentored_by == "PS-VP-ENG"

    def test_json_roundtrip(self):
        person = Person(
            name="Test Person",
            first_name="Test",
            last_name="Person",
            email="test@example.com",
            person_id="PS-99999",
            employment_status="Active",
            current_roles=[
                CurrentRoleAssignment(
                    role_id="RL-001",
                    assignment_type="Primary",
                    allocation_pct=100,
                )
            ],
            skills_inventory=[
                SkillInventoryItem(
                    skill_id="SK-001",
                    skill_name="Python",
                    proficiency_level_actual="Expert",
                )
            ],
            flight_risk="Low",
        )
        data = person.model_dump(mode="json")
        restored = Person.model_validate(data)
        assert restored.person_id == "PS-99999"
        assert restored.current_roles[0].allocation_pct == 100
        assert restored.skills_inventory[0].skill_name == "Python"
        assert restored.flight_risk == "Low"

    def test_any_entity_roundtrip(self):
        person = Person(
            name="AnyEntity Test",
            first_name="Any",
            last_name="Entity",
            email="any@example.com",
            person_id="PS-AE-001",
        )
        data = person.model_dump(mode="json")
        restored = _any_entity_adapter.validate_python(data)
        assert isinstance(restored, Person)
        assert restored.person_id == "PS-AE-001"

    def test_defaults_all_optional(self):
        """All new L05 fields should have defaults — only v0.1 required fields needed."""
        person = Person(
            name="Minimal",
            first_name="Min",
            last_name="Imal",
            email="min@example.com",
        )
        # All new groups should be empty/default
        assert person.person_id == ""
        assert person.current_roles == []
        assert person.skills_inventory == []
        assert person.performance_rating_current is None
        assert person.flight_risk == ""
        assert person.background_check_status.status == ""
        assert person.holds_roles == []
        assert person.mentored_by == ""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.ingestion.resumes.models import (
    CertificationFacts,
    ContactFacts,
    EducationFacts,
    ExperienceFacts,
    FactProvenance,
    LanguageFacts,
    PersonFacts,
    ProjectFacts,
    ResumeFacts,
    SectionFacts,
    SkillFacts,
)


class ExtractedPerson(BaseModel):
    full_name: str | None = None


class ExtractedContact(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    location: str | None = None


class ExtractedExperience(BaseModel):
    organization: str | None = None
    title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class ExtractedEducation(BaseModel):
    institution: str | None = None
    credential: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None


class ExtractedProject(BaseModel):
    name: str | None = None
    role: str | None = None
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class ExtractedCertification(BaseModel):
    name: str | None = None
    issuer: str | None = None
    issued_date: str | None = None
    expiration_date: str | None = None


class ExtractedSkill(BaseModel):
    name: str
    category: str | None = None


class ExtractedLanguage(BaseModel):
    name: str
    proficiency: str | None = None


class ExtractedResumeFacts(BaseModel):
    person: ExtractedPerson | None = None
    contact: ExtractedContact | None = None
    summary: str | None = None
    experiences: list[ExtractedExperience] = Field(default_factory=list)
    education: list[ExtractedEducation] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)
    certifications: list[ExtractedCertification] = Field(default_factory=list)
    skills: list[ExtractedSkill] = Field(default_factory=list)
    languages: list[ExtractedLanguage] = Field(default_factory=list)


class ExtractedSectionFacts(BaseModel):
    section_name: str
    facts: ExtractedResumeFacts = Field(default_factory=ExtractedResumeFacts)


def to_section_facts(
    extracted: ExtractedSectionFacts,
    *,
    source_ref: str,
    fallback_section_name: str,
    raw_text: str,
    text_span: tuple[int, int],
) -> SectionFacts:
    section_name = extracted.section_name or fallback_section_name
    provenance = FactProvenance(
        source_ref=source_ref,
        section=section_name,
        text_span=text_span,
        raw_text=raw_text,
        confidence=0.8,
    )
    facts = extracted.facts
    return SectionFacts(
        section_name=section_name,
        facts=ResumeFacts(
            person=to_person_facts(facts.person, provenance),
            contact=to_contact_facts(facts.contact, provenance),
            summary=facts.summary,
            experiences=[
                to_experience_facts(experience, provenance)
                for experience in facts.experiences
            ],
            education=[
                to_education_facts(education, provenance)
                for education in facts.education
            ],
            projects=[
                to_project_facts(project, provenance) for project in facts.projects
            ],
            certifications=[
                to_certification_facts(certification, provenance)
                for certification in facts.certifications
            ],
            skills=[to_skill_facts(skill, provenance) for skill in facts.skills],
            languages=[
                to_language_facts(language, provenance) for language in facts.languages
            ],
        ),
    )


def to_person_facts(
    person: ExtractedPerson | None,
    provenance: FactProvenance,
) -> PersonFacts | None:
    if person is None or not person.full_name:
        return None
    return PersonFacts(full_name=person.full_name, provenance=provenance)


def to_contact_facts(
    contact: ExtractedContact | None,
    provenance: FactProvenance,
) -> ContactFacts | None:
    if contact is None:
        return None
    return ContactFacts(
        emails=contact.emails,
        phone_numbers=contact.phone_numbers,
        links=contact.links,
        location=contact.location,
        provenance=provenance,
    )


def to_experience_facts(
    experience: ExtractedExperience,
    provenance: FactProvenance,
) -> ExperienceFacts:
    return ExperienceFacts(
        organization=experience.organization,
        title=experience.title,
        location=experience.location,
        start_date=experience.start_date,
        end_date=experience.end_date,
        description=experience.description,
        bullets=experience.bullets,
        technologies=experience.technologies,
        provenance=provenance,
    )


def to_education_facts(
    education: ExtractedEducation,
    provenance: FactProvenance,
) -> EducationFacts:
    return EducationFacts(
        institution=education.institution,
        credential=education.credential,
        field_of_study=education.field_of_study,
        start_date=education.start_date,
        end_date=education.end_date,
        location=education.location,
        provenance=provenance,
    )


def to_project_facts(
    project: ExtractedProject,
    provenance: FactProvenance,
) -> ProjectFacts:
    return ProjectFacts(
        name=project.name,
        role=project.role,
        description=project.description,
        bullets=project.bullets,
        technologies=project.technologies,
        links=project.links,
        provenance=provenance,
    )


def to_certification_facts(
    certification: ExtractedCertification,
    provenance: FactProvenance,
) -> CertificationFacts:
    return CertificationFacts(
        name=certification.name,
        issuer=certification.issuer,
        issued_date=certification.issued_date,
        expiration_date=certification.expiration_date,
        provenance=provenance,
    )


def to_skill_facts(
    skill: ExtractedSkill,
    provenance: FactProvenance,
) -> SkillFacts:
    return SkillFacts(
        name=skill.name,
        category=skill.category,
        provenance=provenance,
    )


def to_language_facts(
    language: ExtractedLanguage,
    provenance: FactProvenance,
) -> LanguageFacts:
    return LanguageFacts(
        name=language.name,
        proficiency=language.proficiency,
        provenance=provenance,
    )

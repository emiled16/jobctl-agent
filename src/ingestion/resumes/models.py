from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    name: str
    heading: str | None = None
    text: str
    start_char: int | None = None
    end_char: int | None = None


class FactProvenance(BaseModel):
    source_ref: str
    section: str | None = None
    page: int | None = None
    text_span: tuple[int, int] | None = None
    raw_text: str
    confidence: float = Field(ge=0.0, le=1.0)


class PersonFacts(BaseModel):
    full_name: str | None = None
    provenance: FactProvenance | None = None


class ContactFacts(BaseModel):
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    location: str | None = None
    provenance: FactProvenance | None = None


class ExperienceFacts(BaseModel):
    organization: str | None = None
    title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    provenance: FactProvenance | None = None


class EducationFacts(BaseModel):
    institution: str | None = None
    credential: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    provenance: FactProvenance | None = None


class ProjectFacts(BaseModel):
    name: str | None = None
    role: str | None = None
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    provenance: FactProvenance | None = None


class CertificationFacts(BaseModel):
    name: str | None = None
    issuer: str | None = None
    issued_date: str | None = None
    expiration_date: str | None = None
    provenance: FactProvenance | None = None


class SkillFacts(BaseModel):
    name: str
    category: str | None = None
    provenance: FactProvenance | None = None


class LanguageFacts(BaseModel):
    name: str
    proficiency: str | None = None
    provenance: FactProvenance | None = None


class ResumeFacts(BaseModel):
    person: PersonFacts | None = None
    contact: ContactFacts | None = None
    summary: str | None = None
    experiences: list[ExperienceFacts] = Field(default_factory=list)
    education: list[EducationFacts] = Field(default_factory=list)
    projects: list[ProjectFacts] = Field(default_factory=list)
    certifications: list[CertificationFacts] = Field(default_factory=list)
    skills: list[SkillFacts] = Field(default_factory=list)
    languages: list[LanguageFacts] = Field(default_factory=list)


class ExtractionWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"]
    related_field: str | None = None
    provenance: FactProvenance | None = None


class SectionFacts(BaseModel):
    section_name: str
    facts: ResumeFacts = Field(default_factory=ResumeFacts)
    warnings: list[ExtractionWarning] = Field(default_factory=list)


class ResumeIngestionResult(BaseModel):
    facts: ResumeFacts
    warnings: list[ExtractionWarning] = Field(default_factory=list)
    validation_errors: list[ExtractionWarning] = Field(default_factory=list)

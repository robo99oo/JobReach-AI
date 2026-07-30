import pytest

from app.services.email_validator import (
    EmailValidationError,
    validate_generated_email,
)


def test_valid_email():
    resume_text = """
    Built a document intelligence solution used by 500 users.
    Reduced manual effort by 60 percent.
    """

    generated_email = """
    Hello,

    I am reaching out regarding Generative AI engineering opportunities.
    In my previous work, I built document intelligence and retrieval-augmented
    generation solutions using Python, FastAPI, FAISS, and large language
    models. One solution supported 500 users and helped reduce manual effort
    by 60 percent. I have also worked on document processing, semantic search,
    prompt validation, API development, and enterprise AI workflows. My
    experience includes building grounded assistants that process complex
    documents and return contextual answers. I would appreciate the
    opportunity to discuss whether my background could support your AI
    engineering team. I have attached my resume and can join immediately.

    Regards,
    Kshiti
    """

    validate_generated_email(
        generated_text=generated_email,
        resume_text=resume_text,
    )


def test_rejects_unsupported_number():
    resume_text = "Built an enterprise AI assistant."

    generated_email = "word " * 100 + "Achieved 95% accuracy."

    with pytest.raises(EmailValidationError):
        validate_generated_email(
            generated_text=generated_email,
            resume_text=resume_text,
        )
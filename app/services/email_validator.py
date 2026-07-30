import re


class EmailValidationError(ValueError):
    """Raised when a generated outreach email fails safety validation."""


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def extract_numbers(text: str) -> set[str]:
    """
    Extracts numbers such as:
    2
    2.5
    60%
    500+
    """
    pattern = r"\b\d+(?:\.\d+)?(?:%|\+)?\b"
    return set(re.findall(pattern, text))


def normalize_number(value: str) -> str:
    return value.rstrip("%+")


def validate_generated_email(
    generated_text: str,
    resume_text: str,
) -> None:
    """
    Validates a generated outreach email.

    Rules:
    - Output must not be empty.
    - Word count must be strictly greater than 90 and strictly less than 160.
    - Every number used in the generated email must exist in the approved
      resume text.
    """

    if not generated_text or not generated_text.strip():
        raise EmailValidationError(
            "Generated email is empty."
        )

    cleaned_email = generated_text.strip()
    word_count = count_words(cleaned_email)

    if not 90 < word_count < 160:
        raise EmailValidationError(
            f"Email contains {word_count} words. "
            "It must contain between 91 and 159 words."
        )

    generated_numbers = extract_numbers(cleaned_email)
    resume_numbers = extract_numbers(resume_text)

    normalized_resume_numbers = {
        normalize_number(number)
        for number in resume_numbers
    }

    unsupported_numbers = {
        number
        for number in generated_numbers
        if normalize_number(number) not in normalized_resume_numbers
    }

    if unsupported_numbers:
        numbers = ", ".join(sorted(unsupported_numbers))

        raise EmailValidationError(
            "Generated email contains unsupported numbers or metrics: "
            f"{numbers}"
        )
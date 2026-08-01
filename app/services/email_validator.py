import re


class EmailValidationError(ValueError):
    """Raised when generated outreach content fails safety checks."""


MIN_BODY_WORDS = 91
MAX_BODY_WORDS = 159


FORBIDDEN_PLACEHOLDERS = (
    "[recipient's name]",
    "[recipient name]",
    "[name]",
    "<recipient>",
    "{{recipient_name}}",
    "{{name}}",
)


FORBIDDEN_QUALITY_PHRASES = (
    "impressed by my skills",
    "valuable assets to your team",
    "align with your interests",
    "align with your team's needs",
    "confident in my ability",
    "strong fit",
    "innovative solutions",
    "contribute to your success",
    "your team's needs",
    "i am immediate joiner",
    "i came across your profile",
    "drive innovation",
    "potential fit",
    "ideal candidate",
    "seasoned expert",
)


WITHOUT_JD_FORBIDDEN_PHRASES = (
    "this role",
    "the role",
    "job posting",
    "job opening",
    "open position",
    "vacancy",
    "hiring requirement",
    "requirements for this role",
    "skills required for this role",
    "i saw your opening",
    "i came across the opening",
)


WITHOUT_JD_COMPANY_CLAIM_PATTERNS = (
    r"\bcontribute to .+ initiatives\b",
    r"\bcontribute to .+ goals\b",
    r"\bcontribute to .+ success\b",
    r"\bcontribute to .+ needs\b",
    r"\balign with .+ initiatives\b",
    r"\balign with .+ goals\b",
    r"\balign with .+ needs\b",
    r"\bbenefit .+\b",
    r"\byour team's current projects\b",
)


SUSPICIOUS_SELF_REFERENCE_PATTERNS = (
    r"\bi was impressed by my\b",
    r"\bi came across your profile and was impressed by my\b",
    r"\bmy skills can be valuable assets\b",
    r"\bi was impressed by my skills\b",
)


THIRD_PERSON_SELF_REFERENCE_PATTERNS = (
    r"\bkshiti has\b",
    r"\bkshiti is\b",
    r"\bkshiti's\b",
    r"\bthe candidate has\b",
    r"\bthe candidate is\b",
    r"\btheir skills\b",
    r"\btheir experience\b",
)


UNSUPPORTED_OUTREACH_PATTERNS = (
    r"\bdrive innovation\b",
    r"\bpotential fit\b",
    r"\byour team's current projects\b",
    r"\bhow my skills might align\b",
    r"\bbenefit [a-z0-9 .'-]+\b",
    r"\bcontribute to [a-z0-9 .'-]+ initiatives\b",
)


def _normalise_text(text: str) -> str:
    """
    Lowercase text and collapse repeated whitespace.
    """

    return re.sub(
        r"\s+",
        " ",
        text.strip().lower(),
    )


def _extract_numbers(text: str) -> set[str]:
    """
    Extract standalone numeric values from text.
    """

    return set(
        re.findall(
            r"(?<!\w)\d+(?:\.\d+)?(?!\w)",
            text,
        )
    )


def _validate_word_count(generated_text: str) -> None:
    words = re.findall(
        r"\b[\w'-]+\b",
        generated_text,
    )

    word_count = len(words)

    if not MIN_BODY_WORDS <= word_count <= MAX_BODY_WORDS:
        raise EmailValidationError(
            f"Email contains {word_count} words. "
            f"It must contain between "
            f"{MIN_BODY_WORDS} and {MAX_BODY_WORDS} words."
        )


def _validate_supported_numbers(
    generated_text: str,
    resume_text: str,
) -> None:
    generated_numbers = _extract_numbers(generated_text)
    resume_numbers = _extract_numbers(resume_text)

    unsupported_numbers = generated_numbers - resume_numbers

    if unsupported_numbers:
        formatted_numbers = ", ".join(
            sorted(unsupported_numbers)
        )

        raise EmailValidationError(
            "Email contains unsupported numeric claims: "
            f"{formatted_numbers}."
        )


def _validate_placeholders(generated_text: str) -> None:
    normalised = _normalise_text(generated_text)

    for placeholder in FORBIDDEN_PLACEHOLDERS:
        if placeholder in normalised:
            raise EmailValidationError(
                "Email contains an unresolved placeholder: "
                f"{placeholder}."
            )


def _validate_quality_phrases(generated_text: str) -> None:
    normalised = _normalise_text(generated_text)

    for phrase in FORBIDDEN_QUALITY_PHRASES:
        if phrase in normalised:
            raise EmailValidationError(
                "Email contains weak or unsupported wording: "
                f"'{phrase}'."
            )


def _validate_without_jd_language(
    generated_text: str,
) -> None:
    normalised = _normalise_text(generated_text)

    for phrase in WITHOUT_JD_FORBIDDEN_PHRASES:
        if phrase in normalised:
            raise EmailValidationError(
                "WITHOUT_JD email contains unsupported "
                f"hiring language: '{phrase}'."
            )

    for pattern in WITHOUT_JD_COMPANY_CLAIM_PATTERNS:
        if re.search(pattern, normalised):
            raise EmailValidationError(
                "WITHOUT_JD email contains an unsupported "
                "company-specific claim."
            )


def _validate_self_reference(generated_text: str) -> None:
    normalised = _normalise_text(generated_text)

    for pattern in SUSPICIOUS_SELF_REFERENCE_PATTERNS:
        if re.search(pattern, normalised):
            raise EmailValidationError(
                "Email contains illogical self-referential wording."
            )


def _validate_first_person_voice(
    generated_text: str,
) -> None:
    normalised = _normalise_text(generated_text)

    for pattern in THIRD_PERSON_SELF_REFERENCE_PATTERNS:
        if re.search(pattern, normalised):
            raise EmailValidationError(
                "Email refers to the candidate in third person. "
                "It must be written entirely in first person."
            )


def _validate_unsupported_outreach_claims(
    generated_text: str,
) -> None:
    normalised = _normalise_text(generated_text)

    for pattern in UNSUPPORTED_OUTREACH_PATTERNS:
        if re.search(pattern, normalised):
            raise EmailValidationError(
                "Email contains vague or unsupported outreach wording."
            )


def _validate_availability_language(
    generated_text: str,
) -> None:
    normalised = _normalise_text(generated_text)

    incorrect_patterns = (
        r"\bi am immediate joiner\b",
        r"\bi am an immediate joiner candidate\b",
    )

    for pattern in incorrect_patterns:
        if re.search(pattern, normalised):
            raise EmailValidationError(
                "Email contains unnatural availability wording. "
                "Use 'I am available to join immediately.'"
            )


def validate_generated_email(
    generated_text: str,
    resume_text: str,
    *,
    is_without_jd: bool = True,
) -> None:
    """
    Validate generated outreach content deterministically.
    """

    if not generated_text.strip():
        raise EmailValidationError(
            "Generated email body is empty."
        )

    _validate_word_count(generated_text)

    _validate_supported_numbers(
        generated_text=generated_text,
        resume_text=resume_text,
    )

    _validate_placeholders(generated_text)
    _validate_quality_phrases(generated_text)
    _validate_self_reference(generated_text)
    _validate_first_person_voice(generated_text)
    _validate_unsupported_outreach_claims(generated_text)
    _validate_availability_language(generated_text)

    if is_without_jd:
        _validate_without_jd_language(generated_text)
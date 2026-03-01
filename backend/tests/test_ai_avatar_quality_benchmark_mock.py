"""Mock benchmark for AI avatar quality (Task 4.10).

This benchmark validates threshold logic without external API dependencies.
"""

from dataclasses import dataclass


@dataclass
class BenchmarkCase:
    prompt_key: str
    expected_keywords: list[str]
    expect_escalate: bool


BASE_CASES = [
    BenchmarkCase("lead_time", ["lead", "delivery", "交期", "Liefer", "納期", "entrega"], False),
    BenchmarkCase("moq", ["minimum", "moq", "最小", "Mindest", "最低", "mínima"], False),
    BenchmarkCase("material", ["material", "steel", "aluminum", "材料", "Material", "materiales"], False),
    BenchmarkCase("tolerance", ["tolerance", "公差", "Toleranz", "公差", "tolerancia"], False),
    BenchmarkCase("cert", ["iso", "cert", "認證", "Zert", "認証", "certific"], False),
    BenchmarkCase("capacity", ["capacity", "產能", "Kapaz", "生産", "capacidad"], False),
    BenchmarkCase("surface", ["surface", "finish", "表面", "Oberfl", "表面", "acabado"], False),
    BenchmarkCase("sample", ["sample", "樣品", "Muster", "サンプル", "muestra"], False),
    BenchmarkCase("shipping", ["shipping", "delivery", "出貨", "Versand", "配送", "envío"], False),
    BenchmarkCase("payment", ["payment", "terms", "付款", "Zahl", "支払い", "pago"], False),
    BenchmarkCase("unknown", [], True),
]


def build_50_cases() -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    for _ in range(5):
        cases.extend(BASE_CASES)
    return cases[:50]


def contains_keyword(answer: str, keywords: list[str]) -> bool:
    normalized = answer.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def _mock_answer(language: str, case: BenchmarkCase) -> dict:
    if case.expect_escalate:
        return {
            "answer": "I need human follow-up for this request.",
            "should_escalate": True,
        }

    keyword = case.expected_keywords[0] if case.expected_keywords else "info"
    suffix = {
        "en": "answer",
        "de": "antwort",
        "ja": "回答",
        "es": "respuesta",
        "zh": "回覆",
    }.get(language, "answer")
    return {
        "answer": f"{keyword} {suffix}",
        "should_escalate": False,
    }


def test_ai_avatar_quality_benchmark_mock_thresholds():
    cases = build_50_cases()

    language_stats = {lang: {"correct": 0, "total": 0} for lang in ["en", "de", "ja", "es"]}
    escalation_checks = {"correct": 0, "total": 0}

    for lang in ["en", "de", "ja", "es", "zh"]:
        for case in cases:
            result = _mock_answer(lang, case)

            if case.expect_escalate:
                escalation_checks["total"] += 1
                if result.get("should_escalate"):
                    escalation_checks["correct"] += 1
                continue

            if lang in language_stats:
                language_stats[lang]["total"] += 1
                if contains_keyword(result.get("answer", ""), case.expected_keywords):
                    language_stats[lang]["correct"] += 1

    en_accuracy = language_stats["en"]["correct"] / max(1, language_stats["en"]["total"])
    de_accuracy = language_stats["de"]["correct"] / max(1, language_stats["de"]["total"])
    ja_accuracy = language_stats["ja"]["correct"] / max(1, language_stats["ja"]["total"])
    es_accuracy = language_stats["es"]["correct"] / max(1, language_stats["es"]["total"])
    escalation_accuracy = escalation_checks["correct"] / max(1, escalation_checks["total"])

    assert en_accuracy >= 0.85, f"English accuracy too low: {en_accuracy:.2%}"
    assert de_accuracy >= 0.75, f"German accuracy too low: {de_accuracy:.2%}"
    assert ja_accuracy >= 0.75, f"Japanese accuracy too low: {ja_accuracy:.2%}"
    assert es_accuracy >= 0.75, f"Spanish accuracy too low: {es_accuracy:.2%}"
    assert escalation_accuracy >= 0.90, f"Escalation accuracy too low: {escalation_accuracy:.2%}"

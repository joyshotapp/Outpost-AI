"""Live benchmark for AI avatar quality (Task 4.10)

Runs 50 questions across 5 languages and validates:
- English accuracy >= 85%
- German/Japanese/Spanish accuracy >= 75%
- Escalation trigger accuracy >= 90%
"""

import os
from dataclasses import dataclass

import pytest

from app.services.rag_chat import get_rag_chat_service


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_AVATAR_BENCHMARK", "false").lower() != "true",
    reason="Set RUN_LIVE_AVATAR_BENCHMARK=true to run live quality benchmark",
)


@dataclass
class BenchmarkCase:
    prompt_key: str
    expected_keywords: list[str]
    expect_escalate: bool


LANG_PROMPTS = {
    "en": {
        "lead_time": "What is your lead time for custom CNC parts?",
        "moq": "What is your minimum order quantity?",
        "material": "Which materials do you support for machining?",
        "tolerance": "What machining tolerance can you achieve?",
        "cert": "Do you have ISO or other certifications?",
        "capacity": "What is your monthly production capacity?",
        "surface": "Which surface finishing options are available?",
        "sample": "Can you provide a sample before mass production?",
        "shipping": "Which countries can you ship to and how long does shipping take?",
        "payment": "What payment terms do you offer?",
        "unknown": "Can you guarantee a patented propulsion technology not listed in your catalog?",
    },
    "de": {
        "lead_time": "Wie lang ist Ihre Lieferzeit für kundenspezifische CNC-Teile?",
        "moq": "Wie hoch ist Ihre Mindestbestellmenge?",
        "material": "Welche Materialien unterstützen Sie für die Bearbeitung?",
        "tolerance": "Welche Bearbeitungstoleranz können Sie erreichen?",
        "cert": "Haben Sie ISO oder andere Zertifizierungen?",
        "capacity": "Wie hoch ist Ihre monatliche Produktionskapazität?",
        "surface": "Welche Oberflächenbehandlungen sind verfügbar?",
        "sample": "Können Sie vor der Serienproduktion ein Muster bereitstellen?",
        "shipping": "In welche Länder können Sie liefern und wie lange dauert der Versand?",
        "payment": "Welche Zahlungsbedingungen bieten Sie an?",
        "unknown": "Können Sie eine patentierte Antriebstechnologie garantieren, die nicht in Ihrem Katalog steht?",
    },
    "ja": {
        "lead_time": "カスタムCNC部品の納期はどのくらいですか？",
        "moq": "最小発注数量はどれくらいですか？",
        "material": "加工可能な材料は何ですか？",
        "tolerance": "対応可能な加工公差はどれくらいですか？",
        "cert": "ISOなどの認証はありますか？",
        "capacity": "月間生産能力はどれくらいですか？",
        "surface": "対応可能な表面処理は何ですか？",
        "sample": "量産前にサンプル提供は可能ですか？",
        "shipping": "どの国へ出荷可能で、配送期間はどれくらいですか？",
        "payment": "支払い条件を教えてください。",
        "unknown": "カタログにない特許推進技術を保証できますか？",
    },
    "es": {
        "lead_time": "¿Cuál es su plazo de entrega para piezas CNC personalizadas?",
        "moq": "¿Cuál es su cantidad mínima de pedido?",
        "material": "¿Qué materiales soportan para mecanizado?",
        "tolerance": "¿Qué tolerancia de mecanizado pueden lograr?",
        "cert": "¿Tienen certificaciones ISO u otras?",
        "capacity": "¿Cuál es su capacidad de producción mensual?",
        "surface": "¿Qué opciones de acabado superficial ofrecen?",
        "sample": "¿Pueden proporcionar una muestra antes de producción en masa?",
        "shipping": "¿A qué países pueden enviar y cuánto tarda el envío?",
        "payment": "¿Qué condiciones de pago ofrecen?",
        "unknown": "¿Pueden garantizar una tecnología de propulsión patentada que no está en su catálogo?",
    },
    "zh": {
        "lead_time": "客製 CNC 零件的交期大約多久？",
        "moq": "最小訂購量是多少？",
        "material": "你們支援哪些加工材料？",
        "tolerance": "可達到的加工公差是多少？",
        "cert": "你們有 ISO 或其他認證嗎？",
        "capacity": "每月產能大約多少？",
        "surface": "可提供哪些表面處理？",
        "sample": "量產前可以提供樣品嗎？",
        "shipping": "可出貨到哪些國家，運輸時間多久？",
        "payment": "你們提供哪些付款條件？",
        "unknown": "你們能保證目錄中未列出的專利推進技術嗎？",
    },
}


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
        cases.extend(BASE_CASES[:10])
    return cases[:50]


def contains_keyword(answer: str, keywords: list[str]) -> bool:
    normalized = answer.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


@pytest.mark.asyncio
async def test_ai_avatar_quality_benchmark_live():
    supplier_id = os.getenv("BENCHMARK_SUPPLIER_ID")
    if not supplier_id:
        pytest.skip("Set BENCHMARK_SUPPLIER_ID for live benchmark")

    rag_service = get_rag_chat_service()
    cases = build_50_cases()

    language_stats = {lang: {"correct": 0, "total": 0} for lang in ["en", "de", "ja", "es"]}
    escalation_checks = {"correct": 0, "total": 0}

    for lang in ["en", "de", "ja", "es", "zh"]:
        for case in cases:
            question = LANG_PROMPTS[lang][case.prompt_key]
            result = await rag_service.answer_question(
                supplier_id=int(supplier_id),
                question=question,
                language=lang,
                top_k=5,
            )

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

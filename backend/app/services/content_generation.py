"""Content generation service — Sprint 9 (Tasks 9.2 + 9.3).

Responsibilities:
  9.2  Claude pipeline:  transcript → 30 LinkedIn posts + 10 SEO articles
  9.3  Quality guard:    strip AI phrases, score tone, deduplicate

The service is async-first and designed to be called from the Celery
content viral pipeline (tasks/content_viral.py) or directly from API tests.

Quality scoring (0-100):
  - Starts at 100
  - Deducts points for each banned phrase found (configurable)
  - Deducts for poor structure (too short, no paragraphs)
  - Deducts for filler opening words
  - Items below QUALITY_PASS_THRESHOLD are flagged for human review
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# ── Quality guard constants ───────────────────────────────────────────────────

QUALITY_PASS_THRESHOLD = 70          # scores below this go to "review" status
FILLER_OPENERS = (
    "certainly", "absolutely", "of course", "great question",
    "i'd be happy", "sure!", "sure,",
)


# ── Prompts ───────────────────────────────────────────────────────────────────

_LINKEDIN_SYSTEM = """You are a B2B content strategist for a precision manufacturing supplier.
Write LinkedIn posts that:
- Sound like a real factory veteran (not a marketer)
- Are 150-250 words each
- Start with a compelling first line (no generic openers)
- Include 2-3 relevant industry insights derived from the transcript
- End with a subtle call-to-action (not salesy)
- Never use these phrases: leverage, harness, game-changer, cutting-edge, synergy,
  revolutionize, delve, certainly, absolutely, as an AI, as a language model
- Each post must be meaningfully different in angle and hook"""

_SEO_SYSTEM = """You are a technical content writer specialising in B2B manufacturing.
Write SEO blog articles that:
- Are 600-900 words each
- Include a compelling H1 title and 3-4 H2 sub-headings (use ## markdown)
- Naturally integrate the given keywords (2-3 times each, not forced)
- Use a factual, expert tone — no fluff
- Include at least one data point or specific manufacturing detail from the transcript
- Never use AI-sounding phrases (certainly, as an AI, leverage, etc.)
- Each article must cover a distinct angle"""

_DEDUP_SYSTEM = """You review batches of AI-generated content for a manufacturing B2B company.
Return ONLY a JSON array of indices (0-based) you want to KEEP.
Keep items if they are MEANINGFULLY DIFFERENT from each other in angle, hook, or core message.
Remove near-duplicates. Always keep at least 1 item."""


class ContentGenerationService:
    """Generate LinkedIn posts, SEO articles, and run quality guard."""

    def __init__(self) -> None:
        self._banned_phrases: list[str] = [
            p.strip().lower()
            for p in settings.CONTENT_AI_BANNED_PHRASES.split(",")
            if p.strip()
        ]

    # ── Public interface ──────────────────────────────────────────────────────

    async def generate_linkedin_posts(
        self,
        transcript: str,
        supplier_name: str,
        industry: str = "precision manufacturing",
        n: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate up to ``n`` LinkedIn posts from a video transcript.

        Returns a list of dicts:
        ``{title, body, hashtags, quality_score, status}``
        """
        n = n or settings.CONTENT_MAX_LINKEDIN_POSTS
        raw_posts = await self._call_claude_batch(
            system=_LINKEDIN_SYSTEM,
            prompt=self._linkedin_prompt(transcript, supplier_name, industry, n),
            expected_key="posts",
        )
        results = []
        seen_titles: set[str] = set()
        for p in raw_posts[:n]:
            body = p.get("body", p.get("content", ""))
            title = p.get("title", body[:60])
            if title in seen_titles:
                continue
            seen_titles.add(title)
            score, flagged = self.quality_check(body)
            results.append({
                "title": title,
                "body": body,
                "hashtags": p.get("hashtags", ""),
                "quality_score": score,
                "status": "draft" if score >= QUALITY_PASS_THRESHOLD else "review",
                "quality_checked": True,
                "flagged_phrases": flagged,
            })
        return results

    async def generate_seo_articles(
        self,
        transcript: str,
        supplier_name: str,
        industry: str = "precision manufacturing",
        n: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate up to ``n`` SEO articles from a video transcript.

        Returns list of dicts:
        ``{title, body, keywords, excerpt, quality_score, status}``
        """
        n = n or settings.CONTENT_MAX_SEO_ARTICLES
        raw_articles = await self._call_claude_batch(
            system=_SEO_SYSTEM,
            prompt=self._seo_prompt(transcript, supplier_name, industry, n),
            expected_key="articles",
        )
        results = []
        for a in raw_articles[:n]:
            body = a.get("body", a.get("content", ""))
            title = a.get("title", "")
            keywords = a.get("keywords", "")
            excerpt = a.get("excerpt", body[:280])
            score, flagged = self.quality_check(body)
            results.append({
                "title": title,
                "body": body,
                "keywords": keywords,
                "excerpt": excerpt,
                "quality_score": score,
                "status": "draft" if score >= QUALITY_PASS_THRESHOLD else "review",
                "quality_checked": True,
                "flagged_phrases": flagged,
            })
        return results

    # ── Quality guard (Task 9.3) ──────────────────────────────────────────────

    def quality_check(self, text: str) -> tuple[int, list[str]]:
        """Score text quality and return ``(score 0-100, list_of_flagged_phrases)``.

        Deductions:
          - 10 pts per banned phrase found (capped at 60 pts total)
          - 15 pts if text < 100 chars
          - 10 pts if no paragraph breaks (single block of text)
          - 5 pts per filler opener detected
        """
        score = 100
        low = text.lower()
        flagged: list[str] = []

        banned_deductions = 0
        for phrase in self._banned_phrases:
            if phrase in low:
                flagged.append(phrase)
                banned_deductions = min(banned_deductions + 10, 60)
        score -= banned_deductions

        if len(text) < 100:
            score -= 15

        if "\n" not in text.strip():
            score -= 10

        for opener in FILLER_OPENERS:
            if low.lstrip().startswith(opener):
                score -= 5
                flagged.append(f"filler_opener:{opener}")
                break

        return max(score, 0), flagged

    def clean_text(self, text: str) -> str:
        """Remove / replace banned phrases from generated text.

        Replaces exact phrase matches with a contextually neutral substitute.
        This is a best-effort pass; human review should be the final gate.
        """
        cleaned = text
        replacements: dict[str, str] = {
            "leverage": "use",
            "harness": "use",
            "game-changer": "significant improvement",
            "cutting-edge": "advanced",
            "synergy": "collaboration",
            "revolutionize": "transform",
            "delve": "explore",
            "certainly": "",
            "absolutely": "",
            "as an ai": "",
            "as a language model": "",
        }
        for phrase, replacement in replacements.items():
            cleaned = re.sub(re.escape(phrase), replacement, cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    # ── Claude API calls ──────────────────────────────────────────────────────

    async def _call_claude_batch(
        self,
        *,
        system: str,
        prompt: str,
        expected_key: str,
    ) -> list[dict[str, Any]]:
        """Call Claude and parse JSON array response.

        Falls back to a single stub item if the API key is not set.
        """
        if not settings.ANTHROPIC_API_KEY:
            logger.info("Claude key not set — returning stub content batch")
            return self._stub_batch(expected_key)

        try:
            import anthropic  # type: ignore[import]

            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=8192,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            # Extract JSON array from markdown code fence if present
            json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
            if json_match:
                raw = json_match.group(1)
            import json
            return json.loads(raw)
        except Exception as exc:
            logger.error("Claude content generation error: %s", exc)
            return self._stub_batch(expected_key)

    def _stub_batch(self, key: str) -> list[dict[str, Any]]:
        if key == "posts":
            return [
                {
                    "title": f"Stub LinkedIn Post {i+1}",
                    "body": f"[stub] This is a generated LinkedIn post number {i+1} about precision manufacturing. "
                            "We focus on quality, speed, and reliability for our global buyers.\n\n"
                            "What sets us apart is our attention to tolerances and on-time delivery.",
                    "hashtags": "manufacturing,quality,precision",
                    "_stub": True,
                }
                for i in range(settings.CONTENT_MAX_LINKEDIN_POSTS)
            ]
        else:  # articles
            return [
                {
                    "title": f"Stub SEO Article {i+1}: Precision Manufacturing Excellence",
                    "body": (
                        f"## Introduction\n[stub] Article {i+1} about precision manufacturing.\n\n"
                        "## Key Capabilities\nOur factory specialises in tight-tolerance CNC machining.\n\n"
                        "## Quality Standards\nWe maintain ISO 9001 certification across all production lines.\n\n"
                        "## Conclusion\nContact us to discuss your next project requirements."
                    ),
                    "keywords": "precision manufacturing,cnc machining,quality control",
                    "excerpt": f"[stub] Overview of our precision manufacturing capabilities — article {i+1}.",
                    "_stub": True,
                }
                for i in range(settings.CONTENT_MAX_SEO_ARTICLES)
            ]

    # ── Prompt builders ───────────────────────────────────────────────────────

    @staticmethod
    def _linkedin_prompt(transcript: str, supplier: str, industry: str, n: int) -> str:
        # Truncate transcript to ~6000 chars to stay within token limits
        t = transcript[:6000]
        return (
            f"Supplier: {supplier}\n"
            f"Industry: {industry}\n\n"
            f"Video transcript:\n{t}\n\n"
            f"Generate exactly {n} unique LinkedIn posts.\n"
            "Return ONLY a valid JSON array with this schema per item:\n"
            '[ { "title": "...", "body": "...", "hashtags": "tag1,tag2,tag3" }, ... ]'
        )

    @staticmethod
    def _seo_prompt(transcript: str, supplier: str, industry: str, n: int) -> str:
        t = transcript[:6000]
        return (
            f"Supplier: {supplier}\n"
            f"Industry: {industry}\n\n"
            f"Video transcript:\n{t}\n\n"
            f"Generate exactly {n} unique SEO blog articles.\n"
            "Return ONLY a valid JSON array with this schema per item:\n"
            '[ { "title": "...", "body": "...(markdown)...", "keywords": "kw1,kw2", "excerpt": "..." }, ... ]'
        )

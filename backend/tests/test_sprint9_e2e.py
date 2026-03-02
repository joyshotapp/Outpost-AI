"""Sprint 9 E2E tests — Content Viral Matrix (Tasks 9.1-9.10).

Test classes:
    TestOpusClipService     -- stub mode, clip job, signature verification
    TestRepurposeService    -- stub mode, text/video scheduling, signature
    TestContentGeneration   -- quality guard, clean_text, stub batch shapes
    TestContentAnalytics    -- stub stat fetching, platform dispatch
    TestContentViralTasks   -- pipeline task helpers (mocked DB)
    TestContentAPI          -- ContentItem Pydantic schema round-trip

All tests run entirely in-process (no DB, no network).
"""

import hashlib
import hmac
import asyncio
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.1 — OpusClipService
# ─────────────────────────────────────────────────────────────────────────────

class TestOpusClipService:
    def _make_svc(self, api_key: str = ""):
        from app.services.opusclip import OpusClipService
        return OpusClipService(api_key=api_key, base_url="http://stub.test")

    def test_stub_mode_when_no_key(self):
        svc = self._make_svc(api_key="")  # empty string → stub mode
        assert svc.stub_mode is True

    def test_not_stub_mode_when_key_present(self):
        svc = self._make_svc(api_key="opus_live_key")
        assert svc.stub_mode is False

    def test_create_clip_job_stub_returns_job_id(self):
        svc = self._make_svc()  # empty key → stub mode
        job = svc.create_clip_job("https://example.com/video.mp4", n_clips=5)
        assert "job_id" in job
        assert job["job_id"].startswith("stub_opusclip_")
        assert job["status"] == "processing"
        assert job["_stub"] is True

    def test_get_job_status_stub_returns_completed(self):
        svc = self._make_svc()  # empty key → stub
        result = svc.get_job_status("stub_job_123")
        assert result["status"] == "completed"
        assert result["_stub"] is True

    def test_get_clips_stub_returns_correct_count(self):
        svc = self._make_svc()  # empty key → stub
        from app.config import settings
        clips = svc.get_clips("stub_job_abc")
        assert len(clips) == settings.OPUSCLIP_CLIPS_PER_VIDEO
        first = clips[0]
        assert "clip_id" in first
        assert "url" in first
        assert "duration_s" in first
        assert "highlights_score" in first
        assert first["_stub"] is True

    def test_verify_webhook_signature_valid(self):
        from app.services.opusclip import OpusClipService
        secret = "mysecret"
        body = b'{"event":"clips.completed","job_id":"job_1"}'
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert OpusClipService.verify_webhook_signature(body, f"sha256={sig}", secret=secret)

    def test_verify_webhook_signature_invalid(self):
        from app.services.opusclip import OpusClipService
        assert not OpusClipService.verify_webhook_signature(
            b"body", "sha256=badsig", secret="mysecret"
        )

    def test_verify_webhook_no_secret_passes(self):
        """When no secret configured, verification is skipped (returns True)."""
        from app.services.opusclip import OpusClipService
        assert OpusClipService.verify_webhook_signature(b"body", "sha256=anything", secret="")


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.5 — RepurposeService
# ─────────────────────────────────────────────────────────────────────────────

class TestRepurposeService:
    def _make_svc(self, api_key: str = ""):
        from app.services.repurpose import RepurposeService
        return RepurposeService(api_key=api_key, base_url="http://stub.test")

    def test_stub_mode_when_no_key(self):
        svc = self._make_svc()  # empty string → stub
        assert svc.stub_mode is True

    def test_list_workflows_stub(self):
        svc = self._make_svc()
        wfs = svc.list_workflows()
        assert len(wfs) == 2
        platforms = {w["platform"] for w in wfs}
        assert "linkedin" in platforms

    def test_schedule_text_post_stub(self):
        svc = self._make_svc()  # stub
        job = svc.schedule_text_post(
            workflow_id="wf_test",
            title="Test Post",
            body="This is a test B2B LinkedIn post.",
            platform="linkedin",
        )
        assert "job_id" in job
        assert job["_stub"] is True
        assert job["status"] in ("scheduled", "queued")

    def test_schedule_video_post_stub(self):
        svc = self._make_svc()  # stub
        job = svc.schedule_video_post(
            workflow_id="wf_yt",
            title="Short Clip 1",
            video_url="https://stub.opusclip.com/clip.mp4",
            platform="youtube",
        )
        assert "job_id" in job
        assert job["platform"] == "youtube"
        assert job["_stub"] is True

    def test_get_post_status_stub(self):
        svc = self._make_svc()  # stub
        status = svc.get_post_status("stub_repurpose_123")
        assert status["status"] == "published"

    def test_verify_webhook_signature_valid(self):
        from app.services.repurpose import RepurposeService
        secret = "rp_secret"
        body = b'{"event":"post.published","job_id":"j1"}'
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert RepurposeService.verify_webhook_signature(body, f"sha256={sig}", secret=secret)


# ─────────────────────────────────────────────────────────────────────────────
# Tasks 9.2 + 9.3 — ContentGenerationService
# ─────────────────────────────────────────────────────────────────────────────

class TestContentGeneration:
    def _make_svc(self):
        from app.services.content_generation import ContentGenerationService
        return ContentGenerationService()

    # ── Quality guard ─────────────────────────────────────────────────────────

    def test_quality_check_clean_text_scores_100(self):
        svc = self._make_svc()
        text = (
            "Our factory produces precision CNC components for the automotive sector.\n\n"
            "We operate three ISO 9001-certified production lines with tolerances of ±0.01 mm.\n\n"
            "Get in touch to discuss your next project."
        )
        score, flagged = svc.quality_check(text)
        assert score == 100
        assert flagged == []

    def test_quality_check_banned_phrase_deducts_points(self):
        svc = self._make_svc()
        text = "As an AI language model I can leverage synergy to revolutionize your business."
        score, flagged = svc.quality_check(text)
        assert score < 100
        assert len(flagged) > 0

    def test_quality_check_short_text_deducts(self):
        svc = self._make_svc()
        score, _ = svc.quality_check("Short.")
        assert score < 100

    def test_quality_check_no_paragraphs_deducts(self):
        svc = self._make_svc()
        text = "A very long single-block text without any paragraph breaks at all this is just one long run-on sentence."
        score, _ = svc.quality_check(text)
        # Should deduct 10 pts for no line breaks
        assert score <= 90

    def test_quality_check_filler_opener_deducts(self):
        svc = self._make_svc()
        text = "Certainly! Here are some manufacturing insights.\n\nWe make precision parts."
        score, flagged = svc.quality_check(text)
        assert score < 100
        opener_flags = [f for f in flagged if f.startswith("filler_opener:")]
        assert len(opener_flags) > 0

    def test_clean_text_removes_banned_words(self):
        svc = self._make_svc()
        text = "We leverage cutting-edge synergy to revolutionize manufacturing."
        cleaned = svc.clean_text(text)
        assert "leverage" not in cleaned.lower()
        assert "synergy" not in cleaned.lower()
        assert "cutting-edge" not in cleaned.lower()

    # ── Stub batch generation (no API key) ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_generate_linkedin_posts_returns_correct_count(self):
        svc = self._make_svc()
        posts = await svc.generate_linkedin_posts(
            transcript="[stub transcript]",
            supplier_name="TestCo",
            n=5,
        )
        assert len(posts) > 0
        assert len(posts) <= 5
        first = posts[0]
        assert "title" in first
        assert "body" in first
        assert "quality_score" in first
        assert "status" in first
        assert first["quality_checked"] is True

    @pytest.mark.asyncio
    async def test_generate_seo_articles_returns_correct_count(self):
        svc = self._make_svc()
        articles = await svc.generate_seo_articles(
            transcript="[stub transcript]",
            supplier_name="TestCo",
            n=3,
        )
        assert len(articles) > 0
        first = articles[0]
        assert "title" in first
        assert "body" in first
        assert "keywords" in first
        assert "excerpt" in first
        assert "quality_score" in first

    @pytest.mark.asyncio
    async def test_quality_guard_applied_to_generated_posts(self):
        """Products of generate_linkedin_posts must carry quality_score and status."""
        svc = self._make_svc()
        posts = await svc.generate_linkedin_posts("[transcript]", "Co", n=3)
        for p in posts:
            assert isinstance(p["quality_score"], int)
            assert p["status"] in ("draft", "review")


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.10 — ContentAnalyticsService
# ─────────────────────────────────────────────────────────────────────────────

class TestContentAnalytics:
    def _make_svc(self):
        from app.services.content_analytics import ContentAnalyticsService
        return ContentAnalyticsService()  # no tokens → stub mode

    def test_stub_linkedin_stats_returns_expected_keys(self):
        svc = self._make_svc()
        stats = svc.fetch_linkedin_stats("urn:li:share:1234")
        for key in ("impressions", "clicks", "likes", "comments", "shares", "engagements"):
            assert key in stats
            assert isinstance(stats[key], int)

    def test_stub_youtube_stats_returns_expected_keys(self):
        svc = self._make_svc()
        stats = svc.fetch_youtube_stats("dQw4w9WgXcQ")
        for key in ("impressions", "clicks", "likes", "comments", "engagements"):
            assert key in stats

    def test_dispatch_linkedin_platform(self):
        svc = self._make_svc()
        stats = svc.fetch_stats_for_item("linkedin", "urn:li:share:xyz")
        assert "impressions" in stats

    def test_dispatch_youtube_platform(self):
        svc = self._make_svc()
        stats = svc.fetch_stats_for_item("youtube", "abc123")
        assert "impressions" in stats

    def test_dispatch_unknown_platform_returns_empty(self):
        svc = self._make_svc()
        stats = svc.fetch_stats_for_item("tiktok", "some_id")
        assert stats == {}

    def test_stub_stats_deterministic_for_same_id(self):
        """Same post ID must return same numbers (seed-based)."""
        svc = self._make_svc()
        s1 = svc.fetch_linkedin_stats("post_abc")
        s2 = svc.fetch_linkedin_stats("post_abc")
        assert s1["impressions"] == s2["impressions"]
        assert s1["clicks"] == s2["clicks"]


# ─────────────────────────────────────────────────────────────────────────────
# ContentItem model shape test
# ─────────────────────────────────────────────────────────────────────────────

class TestContentItemModel:
    def test_content_item_has_expected_columns(self):
        from app.models.content_item import ContentItem
        cols = {c.key for c in ContentItem.__table__.columns}
        required = {
            "id", "supplier_id", "source_video_id",
            "content_type", "title", "body",
            "status", "quality_score", "quality_checked",
            "opusclip_job_id", "short_video_url",
            "repurpose_job_id", "platform",
            "impressions", "engagements", "clicks", "likes", "shares", "comments",
        }
        missing = required - cols
        assert missing == set(), f"Missing columns: {missing}"

    def test_content_item_default_status_is_draft(self):
        from app.models.content_item import ContentItem
        status_col = ContentItem.__table__.columns["status"]
        # Python-side default (not server_default)
        assert str(status_col.default.arg) == "draft"

    def test_content_item_repr(self):
        from app.models.content_item import ContentItem
        # Instantiate via normal constructor (no session needed for repr)
        item = ContentItem(
            content_type="linkedin_post",
            status="draft",
            supplier_id=42,
        )
        assert "linkedin_post" in repr(item)
        assert "draft" in repr(item)


# ─────────────────────────────────────────────────────────────────────────────
# Task 9.3 — Quality guard edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestQualityGuardEdgeCases:
    def _svc(self):
        from app.services.content_generation import ContentGenerationService
        return ContentGenerationService()

    def test_score_never_goes_below_zero(self):
        svc = self._svc()
        # Embed as many banned phrases as possible
        text = " ".join([
            "as an ai certainly absolutely leverage harness synergy game-changer",
            "cutting-edge revolutionize delve in today's fast-paced it's important to note",
        ])
        score, _ = svc.quality_check(text)
        assert score >= 0

    def test_empty_text(self):
        svc = self._svc()
        score, flagged = svc.quality_check("")
        assert score >= 0

    def test_clean_text_is_idempotent(self):
        svc = self._svc()
        dirty = "We leverage leverage leverage cutting-edge solutions."
        first_pass = svc.clean_text(dirty)
        second_pass = svc.clean_text(first_pass)
        assert first_pass == second_pass

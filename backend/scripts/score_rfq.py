"""Score RFQ #1 with LeadScoringEngine and also run Claude text analysis."""
import asyncio
import sys

async def main():
    from app.database import async_session_maker
    from app.models import RFQ
    from app.services.lead_scoring import get_lead_scoring_engine
    from app.services.claude import get_claude_service
    from sqlalchemy import select, update

    engine = get_lead_scoring_engine()
    claude = get_claude_service()

    async with async_session_maker() as db:
        result = await db.execute(select(RFQ).where(RFQ.id == 1))
        rfq = result.scalar_one()

        print(f"--- RFQ #{rfq.id}: {rfq.title} ---")
        print(f"Description: {rfq.description[:120]}...")
        print()

        # Build rfq_text string
        rfq_text = f"{rfq.title}\n\n{rfq.description}"
        if rfq.specifications:
            rfq_text += f"\n\nSpecs: {rfq.specifications}"

        # 1. Lead Scoring (pass rfq_text as string, with buyer info)
        score_result = await engine.score_rfq(
            rfq_text=rfq_text,
            buyer_company_name="Weber Aerospace GmbH",
            buyer_domain="aerospace.de",
        )
        lead_score = score_result["lead_score"]
        lead_grade = score_result["lead_grade"]
        print(f"[LeadScore] Score: {lead_score} | Grade: {lead_grade}")
        breakdown = score_result.get("scoring_breakdown", {})
        for k, v in breakdown.items():
            print(f"  {k}: score={v.get('score','?')} weight={v.get('weight','?')}")
        print()

        # 2. Claude RFQ text analysis
        print("[Claude] Analyzing RFQ text...")
        try:
            analysis = await claude.analyze_rfq_text(
                rfq_text=rfq_text,
                supplier_context="Precision CNC machining, aluminum casting, ISO9001 certified",
            )
            ai_summary = analysis.get("summary", analysis.get("analysis", str(analysis)[:400]))
            print(f"[Claude] {ai_summary[:500]}")
        except Exception as e:
            print(f"[Claude] Error: {e}")
            ai_summary = None

        # 3. Save results to DB
        update_vals = {"lead_score": lead_score, "lead_grade": lead_grade}
        if ai_summary:
            update_vals["ai_summary"] = ai_summary
        await db.execute(update(RFQ).where(RFQ.id == 1).values(**update_vals))
        await db.commit()
        print()
        print(f"✅ RFQ #{rfq.id} scored and saved: Score={lead_score} Grade={lead_grade}")

asyncio.run(main())

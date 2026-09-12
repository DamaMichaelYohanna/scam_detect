"""
Test Pipeline Script
Allows testing the heuristic detector, Exa.ai live extraction, and OpenAI analysis
with mock messages directly from the command line.
"""

import asyncio
import sys

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.config import settings
from app.services.detector_service import detector_service
from app.services.exa_service import exa_service
from app.services.openai_service import openai_service


TEST_CASES = [
    {
        "name": "Crypto Phishing / Airdrop Drainer",
        "text": "🚨 OFFICIAL AIRDROP LIVE! Claim your free $5000 USDT reward instantly at https://unisvvap-airdrop.xyz/claim before it ends! Connect wallet now.",
    },
    {
        "name": "Telegram Impersonation Support",
        "text": "Hello, I am Telegram Admin Helpdesk. Your account has suspicious activity. Please DM admin @support_helpdesk_123 or validate wallet at https://wallet-rectify-security.top to prevent suspension.",
    },
    {
        "name": "Legitimate Crypto Conversation",
        "text": "Hey everyone, check out the new Python 3.12 release notes here: https://docs.python.org/3/whatsnew/3.12.html. The performance improvements look great!",
    },
    {
        "name": "Casual Safe Chat",
        "text": "Good morning everyone! What are we working on today?",
    },
]


async def run_test_case(case: dict):
    print("=" * 70)
    print(f"TEST CASE: {case['name']}")
    print(f"Message: \"{case['text']}\"")
    print("-" * 70)

    # 1. Heuristic Scan
    inspection = detector_service.inspect_message(case["text"])
    print(f"[1] Detector Service Inspection:")
    print(f"    - Should Deep Scan: {inspection.should_deep_scan}")
    print(f"    - URLs Found: {inspection.urls}")
    print(f"    - Crypto Addresses: {inspection.crypto_addresses}")
    print(f"    - Trigger Keywords: {inspection.matched_keywords}")
    print(f"    - Quick Reason: {inspection.quick_reason}")

    if not inspection.should_deep_scan:
        print("\n--> [Result]: Message deemed SAFE by heuristic filter. Skipping Exa/OpenAI.")
        return

    # Check AI API keys
    has_ai_key = bool(settings.OPENAI_API_KEY or settings.GEMINI_API_KEY)
    if not has_ai_key:
        print("\n⚠️ [Notice]: Neither OPENAI_API_KEY nor GEMINI_API_KEY is configured in .env.")
        return

    # 2. Exa Live Extraction
    context_str = ""
    if settings.EXA_API_KEY:
        print("\n[2] Fetching Live Web Context via Exa.ai...")
        exa_result = await exa_service.extract_context(
            urls=inspection.urls,
            message_text=case["text"],
            matched_keywords=inspection.matched_keywords,
        )
        context_str = exa_result.to_combined_context()
        print(f"    - Exa Context Length: {len(context_str)} characters")
        if exa_result.page_contents:
            print("    - Preview of Fetched Page:\n" + "\n".join("      " + l for l in exa_result.page_contents.splitlines()[:5]))
    else:
        print("\n[2] Exa.ai: EXA_API_KEY not set; evaluating message content directly.")

    # 3. AI Classification (OpenAI / Gemini)
    from app.services.analyzer_service import analyzer_service
    print(f"\n[3] Running Scam Threat Analysis with [{settings.AI_PROVIDER.upper()}]...")
    analysis = await analyzer_service.analyze_message(
        message_text=case["text"],
        urls=inspection.urls,
        crypto_addresses=inspection.crypto_addresses,
        exa_context=context_str,
    )

    if analysis:
        print(f"\n🎯 [AI Threat Evaluation Result]:")
        print(f"    - Provider Used: {settings.AI_PROVIDER.upper()}")
        print(f"    - Is Scam: {analysis.is_scam}")
        print(f"    - Risk Level: {analysis.risk_level}")
        print(f"    - Confidence: {analysis.confidence * 100:.1f}%")
        print(f"    - Scam Type: {analysis.scam_type}")
        print(f"    - Summary: {analysis.short_summary}")
        print(f"    - Safety Advice: {analysis.warning_advice}")
    else:
        print("\n❌ AI analysis returned no result.")


async def main():
    print("Testing Telegram Anti-Scam Bot Analysis Pipeline\n")
    for test in TEST_CASES:
        await run_test_case(test)
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())

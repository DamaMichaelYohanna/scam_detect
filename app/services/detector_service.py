import re
from typing import List, Set
from pydantic import BaseModel, Field

# URL extraction regex pattern
URL_PATTERN = re.compile(
    r'(?:https?:\/\/|www\.)[^\s<>"\']+|[a-zA-Z0-9.-]+\.(?:com|org|net|io|xyz|app|me|site|link|top|vip|info|cc|buzz|live|biz|club|online|tech|art|trade|finance|cx|is|tg|bot)[^\s<>"\']*',
    re.IGNORECASE,
)

# Crypto address patterns
ETH_ADDRESS_PATTERN = re.compile(r'\b0x[a-fA-F0-9]{40}\b')
SOL_ADDRESS_PATTERN = re.compile(r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b')
BTC_ADDRESS_PATTERN = re.compile(r'\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b')

# Suspicious / Scam trigger keywords & phrases
SCAM_KEYWORDS = [
    # Crypto / Web3
    r'\bairdrop\b',
    r'\bfree\s+mint\b',
    r'\bclaim\s+(?:now|bonus|reward|token|airdrop|nft|sol|eth|usdt)\b',
    r'\bconnect\s+wallet\b',
    r'\bseed\s+phrase\b',
    r'\bprivate\s+key\b',
    r'\bpresale\b',
    r'\bwhitelist\b',
    r'\bswap\s+instant\b',
    r'\bvalidate\s+wallet\b',
    r'\bwallet\s+rectif(?:y|ication)\b',
    r'\bdoubler\b',
    r'\bguaranteed\s+(?:profit|return|income)\b',
    # Impersonation & Support
    r'\bdm\s+admin\b',
    r'\bcontact\s+(?:support|admin|helpdesk)\b',
    r'\bofficial\s+support\b',
    r'\bhelpdesk\b',
    r'\bcustomer\s+care\b',
    # General scams / phishing
    r'\btelegram\s+premium\s+free\b',
    r'\bfree\s+nitro\b',
    r'\bgift\s+card\s+code\b',
    r'\bcongratulations\s+you\s+won\b',
    r'\blucky\s+winner\b',
    r'\binvestment\s+opportunity\b',
    r'\bpassive\s+income\b',
    r'\bearn\s+\$?\d+\s+(?:daily|hourly|per\s+day)\b',
    r'\bverify\s+your\s+account\b',
    r'\baccount\s+(?:suspended|locked|blocked)\b',
]

COMPILED_KEYWORDS = [re.compile(kw, re.IGNORECASE) for kw in SCAM_KEYWORDS]


class DetectionInspection(BaseModel):
    has_urls: bool = False
    urls: List[str] = Field(default_factory=list)
    crypto_addresses: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    should_deep_scan: bool = False
    quick_reason: str = ""


class DetectorService:
    @staticmethod
    def inspect_message(text: str) -> DetectionInspection:
        if not text:
            return DetectionInspection()

        # 1. Extract URLs
        raw_urls = URL_PATTERN.findall(text)
        urls: List[str] = []
        for u in raw_urls:
            # Clean trailing punctuation
            clean_url = u.rstrip('.,!?;:)')
            if clean_url and clean_url not in urls:
                urls.append(clean_url)

        # 2. Extract Crypto Addresses
        crypto_addresses: Set[str] = set()
        for eth in ETH_ADDRESS_PATTERN.findall(text):
            crypto_addresses.add(f"ETH:{eth}")
        for btc in BTC_ADDRESS_PATTERN.findall(text):
            crypto_addresses.add(f"BTC:{btc}")
        # Only check SOL if crypto-relevant keywords exist or URL present to reduce base58 false positives
        if urls or any(k in text.lower() for k in ["sol", "solana", "phantom", "mint", "pump", "raydium", "token"]):
            for sol in SOL_ADDRESS_PATTERN.findall(text):
                if not sol.startswith("http") and len(sol) >= 32:
                    crypto_addresses.add(f"SOL:{sol}")

        # 3. Match Scam Keywords
        matched_keywords: List[str] = []
        for kw_regex in COMPILED_KEYWORDS:
            match = kw_regex.search(text)
            if match:
                matched_keywords.append(match.group(0))

        # 4. Determine if deep scan (Exa + OpenAI) is needed
        should_deep_scan = bool(urls or crypto_addresses or matched_keywords)

        reasons = []
        if urls:
            reasons.append(f"{len(urls)} link(s) found")
        if crypto_addresses:
            reasons.append(f"{len(crypto_addresses)} crypto address(es)")
        if matched_keywords:
            reasons.append(f"matched trigger terms ({', '.join(matched_keywords[:3])})")

        quick_reason = "; ".join(reasons) if reasons else "No suspicious signals detected"

        return DetectionInspection(
            has_urls=bool(urls),
            urls=urls,
            crypto_addresses=list(crypto_addresses),
            matched_keywords=matched_keywords,
            should_deep_scan=should_deep_scan,
            quick_reason=quick_reason,
        )


detector_service = DetectorService()

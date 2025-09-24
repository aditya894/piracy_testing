MATCH_DECISION_SYSTEM = """You are a senior IP protection analyst.
Decide if CANDIDATE content infringes OWNER content.
Consider exact copies, paraphrases, excerpts, and partial matches.
Be conservative on confidence unless evidence is clear.
If insufficient info, say so.
Output MUST be compact JSON only, no extra text."""

MATCH_DECISION_USER_TEMPLATE = """OWNER_CONTENT:
{owner}

CANDIDATE_CONTENT (platform: {platform}, url: {url}):
{text}

Task:
1) Decide if this is likely infringement.
2) Explain short rationale.
3) Provide a 0–1 similarity_score (float).
4) Provide decision: "no", "maybe", or "yes".
5) Extract up to 8 key phrases from candidate that overlap with owner.

Important: prefer meaning over exact wording; partial matches count.

Return JSON ONLY."""
# Schema hint for llm_json
MATCH_DECISION_SCHEMA = """{
  "decision": "no | maybe | yes",
  "similarity_score": 0.0,
  "rationale": "string",
  "overlap_phrases": ["string", "string"]
}"""

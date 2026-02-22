"""
AI Scorer — OpenRouter Integration
===================================
Calls free LLMs via the OpenRouter chat completions API to produce:

  • narrative  – 2-3 sentence personalised summary of the resume.
  • tips       – 3-5 actionable, role-specific improvement tips.

Model fallback chain: tries each free model in order until one succeeds.
On any error (network, auth, all rate-limited) returns graceful fallback
content so the rest of the application is never broken.
"""

import json
import logging
import time

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free models tried in order — first available wins.
# Verified 2026-02: gemma-3-27b and llama-3.3-70b work when not rate-limited.
# openrouter/auto is the guaranteed last-resort (routes to any available free model).
FREE_MODELS = [
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "openrouter/auto",              # always available — picks any free model
]

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_ai_feedback(
    resume_text: str,
    target_role: str,
    score: int,
    breakdown: dict,
    missing_skills: list,
    api_key: str = "",
) -> dict:
    """
    Call OpenRouter to get AI-powered feedback for a resume.

    Parameters
    ----------
    resume_text   : raw resume text (truncated internally to ~3 000 chars)
    target_role   : e.g. "Backend Developer"
    score         : rule-based ATS score 0-100
    breakdown     : dict of sub-scores {"Keyword Match": 32, ...}
    missing_skills: list of skill names the candidate is missing
    api_key       : OpenRouter API key (Bearer token)

    Returns
    -------
    {
        "narrative":  str,   # 2-3 sentence paragraph
        "tips":       list,  # 3-5 strings
        "ai_powered": bool,  # False if we fell back to static content
        "model":      str,   # Model that succeeded (or "" on failure)
    }
    """
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not configured – skipping AI feedback.")
        return _fallback()

    try:
        import requests  # imported lazily so the module loads without requests
    except ImportError:
        logger.error("'requests' library not installed.")
        return _fallback()

    # Truncate resume text to keep prompt small (free-tier context limits)
    snippet = resume_text[:3000].strip()
    prompt = _build_prompt(snippet, target_role, score, breakdown, missing_skills)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resumeiq.app",   # recommended by OpenRouter
        "X-Title": "ResumeIQ",
    }

    last_error = None
    for model in FREE_MODELS:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert ATS resume coach. "
                        "Give concise, actionable, role-specific feedback. "
                        "Respond with valid JSON only — no markdown, no prose outside JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 512,
            "temperature": 0.6,
        }

        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=20)

            # 429 = rate-limited on this model → try next
            if resp.status_code == 429:
                logger.info("Model %s rate-limited, trying next...", model)
                last_error = "429 rate-limited"
                continue

            # 404 = model unavailable → try next
            if resp.status_code == 404:
                logger.info("Model %s not found, trying next...", model)
                last_error = "404 not found"
                continue

            resp.raise_for_status()
            data = resp.json()

            raw_content = data["choices"][0]["message"]["content"].strip()
            result = _parse_llm_json(raw_content)
            result["ai_powered"] = True
            result["model"] = model
            logger.info("AI feedback obtained via %s", model)
            return result

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.warning("Unexpected response from %s: %s", model, e)
            last_error = str(e)
            continue
        except Exception as e:
            logger.warning("OpenRouter call failed for %s: %s", model, e)
            last_error = str(e)
            # Network errors → don't keep trying; API might be down
            break

    logger.warning("All models failed. Last error: %s", last_error)
    return _fallback()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_prompt(
    snippet: str,
    target_role: str,
    score: int,
    breakdown: dict,
    missing_skills: list,
) -> str:
    missing_str = ", ".join(missing_skills[:10]) if missing_skills else "none identified"
    breakdown_str = " | ".join(f"{k}: {v}" for k, v in breakdown.items())

    return (
        f'You are reviewing a resume for the role: "{target_role}"\n\n'
        f"ATS Score: {score}/100\n"
        f"Score Breakdown: {breakdown_str}\n"
        f"Missing Key Skills: {missing_str}\n\n"
        f"Resume Excerpt:\n{snippet}\n\n"
        'Respond ONLY with a JSON object (no markdown, no extra text) in exactly this shape:\n'
        '{\n'
        '  "narrative": "<2-3 sentences: personalised overall assessment>",\n'
        '  "tips": [\n'
        '    "<tip 1 — specific and actionable>",\n'
        '    "<tip 2>",\n'
        '    "<tip 3>",\n'
        '    "<tip 4>"\n'
        '  ]\n'
        '}'
    )


def _parse_llm_json(raw: str) -> dict:
    """
    Attempt to parse the LLM JSON response.
    Handles markdown fences and minor formatting issues.
    """
    # Strip markdown code fences if present
    if "```" in raw:
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()

    parsed = json.loads(raw)

    narrative = parsed.get("narrative", "")
    tips = parsed.get("tips", [])

    if not isinstance(narrative, str):
        narrative = str(narrative)
    if not isinstance(tips, list):
        tips = [str(tips)]

    return {
        "narrative": narrative.strip(),
        "tips": [str(t).strip() for t in tips if t],
    }


def _fallback() -> dict:
    return {
        "narrative": (
            "AI feedback is temporarily unavailable. "
            "Your score is based on our rule-based ATS analysis. "
            "Review the tips below to improve your resume."
        ),
        "tips": [],
        "ai_powered": False,
        "model": "",
    }

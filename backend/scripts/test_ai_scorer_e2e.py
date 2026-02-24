"""
End-to-end test of the AI scorer against a real resume snippet.
Run: python test_ai_scorer_e2e.py
"""
import sys
import os

# Make sure we can import from utils/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ai_scorer import get_ai_feedback

RESUME_SNIPPET = """
John Doe
johndoe@gmail.com | +1-555-0199 | github.com/johndoe

SUMMARY
Software Engineer with 3+ years building scalable backend services using Python,
Flask, and PostgreSQL. Comfortable with Docker and CI/CD pipelines.

SKILLS
Python, Flask, JavaScript, SQL, Git, Docker, REST API, Linux, PostgreSQL

EXPERIENCE
Backend Developer – Tech Corp (2022–Present)
- Built microservices architecture serving 50k+ daily users
- Reduced API response time by 35% via Redis caching
- Led a team of 3 engineers on a payment integration project

Software Engineering Intern – StartupXYZ (2021)
- Developed REST APIs using Django REST Framework
- Wrote unit tests achieving 80% code coverage

EDUCATION
B.Tech in Computer Science – State University (2021)

CERTIFICATIONS
AWS Certified Developer – Associate (2023)
"""

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

print("Running AI Scorer end-to-end test...")
print("=" * 60)

result = get_ai_feedback(
    resume_text=RESUME_SNIPPET,
    target_role="Backend Developer",
    score=72,
    breakdown={
        "Keyword Match": 32,
        "Skills Match": 20,
        "Experience": 12,
        "Education": 4,
        "Formatting": 4,
    },
    missing_skills=["Kubernetes", "Kafka", "AWS", "GraphQL", "Redis"],
    api_key=API_KEY,
)

print(f"AI Powered: {result.get('ai_powered')}")
print(f"\nNarrative:\n{result.get('narrative')}")
print(f"\nTips ({len(result.get('tips', []))}):")
for i, tip in enumerate(result.get('tips', []), 1):
    print(f"  {i}. {tip}")

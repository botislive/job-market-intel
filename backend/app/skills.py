import re

STAFFING_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js", "Angular",
    "Vue", "Go", "Rust", "C++", "C#", ".NET", "Ruby", "PHP", "Swift", "Kotlin",
    "AWS", "Azure", "GCP", "Google Cloud", "Kubernetes", "Docker", "Terraform",
    "DevOps", "CI/CD", "Jenkins", "GitLab", "GitHub Actions",
    "SAP", "S/4HANA", "ABAP", "FICO", "ServiceNow", "Salesforce", "Snowflake",
    "Databricks", "Oracle", "Workday", "PeopleSoft",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Machine Learning", "AI", "LLM", "Data Engineering", "ETL", "Spark",
    "Tableau", "Power BI", "Agile", "Scrum", "REST API", "GraphQL",
    "Linux", "Networking", "Cybersecurity", "SOC", "IAM",
    "Procurement", "Supply Chain", "Sourcing",
]


def extract_skills(text: str) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    lower = text.lower()
    for skill in STAFFING_SKILLS:
        pattern = re.escape(skill.lower())
        if re.search(rf"\b{pattern}\b", lower):
            found.append(skill)
    return found[:12]


def skills_to_string(skills: list[str]) -> str:
    return ", ".join(skills)

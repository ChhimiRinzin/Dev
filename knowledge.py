"""Simple transparent local keyword retrieval (not embedding-based RAG)."""
import re
from collections import Counter

DOCS = {
    'Python environments': 'A Python virtual environment isolates packages. Verify python --version and python -m pip --version refer to the intended environment.',
    'Package installation': 'Wheel availability depends on both Python version and operating system. Prefer binary wheels and pinned versions before compiling a native dependency.',
    'Database connectivity': 'Database connection failures require checking host, port, service state, network policy and authentication separately. Do not expose credentials in logs.',
    'Deployment diagnosis': 'Build pipeline failures should be investigated from the first meaningful exception. Environment variables may differ between local and deployed environments.',
    'Permissions': 'A denied operation may mean missing OS access rights, cloud IAM permissions or an expired token. Use minimum necessary permissions.',
}

def search_docs(query: str, limit: int = 2) -> list[tuple[str, str]]:
    words = Counter(re.findall(r'[a-z]{3,}', query.lower()))
    scores = []
    for title, content in DOCS.items():
        tokens = Counter(re.findall(r'[a-z]{3,}', (title + ' ' + content).lower()))
        score = sum(min(count, tokens[token]) for token, count in words.items())
        if score:
            scores.append((score, title, content))
    return [(title, content) for _, title, content in sorted(scores, reverse=True)[:limit]]

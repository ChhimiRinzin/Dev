"""Offline, deterministic developer issue triage. No execution of user content."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re

@dataclass(frozen=True)
class Finding:
    category: str
    title: str
    evidence: str
    explanation: str
    actions: tuple[str, ...]
    score: int
    source: str = 'Rules engine'

RULES = [
    ('dependency', 'Missing Python module', r'(?:ModuleNotFoundError|ImportError):\s*(?:No module named\s*)?[\'\"]?([\w.]+)', 'A required Python package/module is missing or unavailable in the selected environment.', ('Check the active virtual environment and interpreter.', 'Install the dependency using python -m pip, then rerun the application.', 'Check that the import name matches the package name.'), 95),
    ('dependency', 'Python package build failure', r'(?:Failed building wheel for\s+([\w.-]+)|Could not find a package configuration file provided by\s+[\'\"]?([\w.-]+))', 'A dependency could not be installed from a wheel or compiled from source.', ('Check Python version and availability of binary wheels.', 'Try a compatible package version in a fresh virtual environment.', 'Read the earliest build error before attempting system-level changes.'), 94),
    ('database', 'Database connection refused', r'(?:connection refused|could not connect to server|ECONNREFUSED)', 'The configured database endpoint is not accepting a connection.', ('Confirm database service status and configured host/port.', 'Check network routes and firewall rules.', 'Verify credentials without pasting secrets into logs.'), 88),
    ('authentication', 'Authentication or permission failure', r'(?:401 Unauthorized|403 Forbidden|permission denied|AccessDenied|authentication failed)', 'The requested operation was denied or the credentials were rejected.', ('Verify the authenticated identity and required role.', 'Check file or service permissions.', 'Rotate any credentials exposed in logs.'), 84),
    ('network', 'Network or DNS failure', r'(?:Name or service not known|Temporary failure in name resolution|ENOTFOUND|Network is unreachable|DNS_PROBE_FINISHED_NXDOMAIN)', 'The target hostname could not be resolved or reached.', ('Check the hostname and network connectivity.', 'Verify DNS resolution.', 'Inspect proxy and firewall settings.'), 84),
    ('deployment', 'Deployment/build failure', r'(?:Build failed|Deployment failed|Error: Command .* exited with 1|npm ERR!)', 'A build or deployment command failed; inspect preceding output for the original cause.', ('Find the first meaningful build error.', 'Reproduce the build locally with pinned dependencies.', 'Confirm required environment variables are set securely.'), 70),
    ('syntax', 'Python syntax error', r'(?:SyntaxError:|IndentationError:|TabError:)', 'Python could not parse the source file.', ('Inspect the file and line indicated in the traceback.', 'Check indentation, delimiters and syntax.', 'Run python -m compileall on the project.'), 92),
    ('runtime', 'Python runtime exception', r'(?:TypeError:|ValueError:|KeyError:|AttributeError:|IndexError:|ZeroDivisionError:)', 'The program raised a runtime exception.', ('Read the exception message and the last relevant traceback frame.', 'Check the values and types passed to the failing function.', 'Add a targeted regression test.'), 80),
    ('performance', 'Memory exhaustion', r'(?:CUDA out of memory|MemoryError|OOMKilled|OutOfMemoryError)', 'The process appears to have exhausted its memory allocation.', ('Inspect memory usage and input sizes.', 'Reduce batch size or concurrency.', 'Profile before increasing resource limits.'), 92),
]

SECRET_PATTERNS = [
    re.compile(r'(?i)\b(password|passwd|api[_-]?key|secret|token|authorization)\s*[:=]\s*([^\s,;]+)'),
    re.compile(r'\b(?:ghp_|github_pat_|sk-)[A-Za-z0-9_-]{12,}\b'),
]

def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        if pattern.groups == 2:
            text = pattern.sub(lambda m: m.group(1) + '=[REDACTED]', text)
        else:
            text = pattern.sub('[REDACTED]', text)
    return text

def analyze(text: str, max_chars: int = 100_000) -> list[Finding]:
    text = redact(text[:max_chars])
    findings: list[Finding] = []
    for category, title, pattern, explanation, actions, score in RULES:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Prefer a whole line of evidence, but do not leak a raw multiline trace.
            start = text.rfind('\n', 0, match.start()) + 1
            end = text.find('\n', match.end())
            if end < 0:
                end = len(text)
            evidence = text[start:end].strip()[:350]
            evidence = redact(evidence)
            findings.append(Finding(category, title, evidence, explanation, actions, score))
    return sorted(findings, key=lambda finding: -finding.score)

def export_report(findings: list[Finding], redacted_input: str) -> str:
    lines = ['# DevSentinel Investigation', '', 'Local rule-based analysis; findings are hypotheses, not verified fixes.', '']
    if not findings:
        lines.append('No known signature detected. Gather a full traceback and additional context.')
    for idx, finding in enumerate(findings, 1):
        lines.extend([f'## {idx}. {finding.title}', f'Category: {finding.category}', f'Evidence: `{finding.evidence}`', finding.explanation, '', 'Suggested checks:'])
        lines.extend(f'- {action}' for action in finding.actions)
        lines.append('')
    lines.extend(['## Redacted input', '```text', redact(redacted_input)[:20000].replace('```', '` ` `'), '```'])
    return '\n'.join(lines)

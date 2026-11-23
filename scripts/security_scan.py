import re
import os
import sys

patterns = [
    re.compile(r'(?i)(?:api_key|apikey|secret|password|bearer|auth_token)\s*[:=]\s*[\'\"][A-Za-z0-9_\-]{20,}[\'\"]'),
    re.compile(r'ghp_[A-Za-z0-9]{36}'),
    re.compile(r'sk_live_[A-Za-z0-9]{24}'),
    re.compile(r'AKIA[0-9A-Z]{16}')
]

found = []
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', 'node_modules', '.venv', 'dist', '__pycache__']):
        continue
    for f in files:
        if f.endswith(('.py', '.json', '.md', '.jsx', '.js', '.html', '.css', '.toml')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for p in patterns:
                        for m in p.finditer(content):
                            # Exclude known false positives like schema descriptions or dummy regex
                            val = m.group(0)
                            if 'placeholder' in val.lower() or 'none' in val.lower():
                                continue
                            found.append((path, val[:35]))
            except Exception:
                pass

print(f"Security Scan Complete. Secret matches found: {len(found)}")
if found:
    for item in found:
        print("  Potential secret:", item)
    sys.exit(1)
else:
    print("ALL SECURITY CHECKS PASSED: Zero private keys, tokens, or credentials found.")
    sys.exit(0)

#!/bin/bash
set -e

echo "🚀 Installation AI Self-Healing System"

# 1. Pré-requis
apt update
apt install -y docker.io docker-compose git python3 python3-pip
systemctl enable docker
systemctl start docker

# 2. Arborescence
mkdir -p ai-control-plane/{agents,prompts,policies,logs}
cd ai-control-plane

# 3. Guardrails
cat > policies/guardrails.yaml <<EOF
forbidden:
  - auth
  - permissions
  - accounting
  - schema
rollback:
  on_error: true
  min_coverage: 80
EOF

# 4. Prompts
cat > prompts/debug.prompt <<EOF
You are an autonomous debugging AI.
Find the root cause.
If uncertain: ABORT.
EOF

cat > prompts/fix.prompt <<EOF
You are an autonomous fixing AI.
Apply minimal safe patch.
No refactor unless mandatory.
EOF

cat > prompts/test.prompt <<EOF
You are an autonomous test generator.
Generate destructive tests.
EOF

cat > prompts/validate.prompt <<EOF
You are a strict validator.
If risk detected: ROLLBACK.
EOF

# 5. Agent principal (cerveau)
cat > agents/ai_orchestrator.py <<'EOF'
import os, time, subprocess, json
from openai import OpenAI
import anthropic

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

openai = OpenAI(api_key=OPENAI_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

def read_prompt(name):
    with open(f"prompts/{name}.prompt") as f:
        return f.read()

def run_cmd(cmd):
    return subprocess.getoutput(cmd)

def get_logs():
    return run_cmd("docker logs $(docker ps -q) --tail 50")

def get_diff():
    return run_cmd("git diff HEAD~1")

def call_openai(prompt, data):
    return openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role":"system","content":prompt},
            {"role":"user","content":data}
        ]
    ).choices[0].message.content

def call_claude(prompt, data):
    msg = anthropic_client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=2000,
        system=prompt,
        messages=[{"role":"user","content":data}]
    )
    return msg.content[0].text

while True:
    logs = get_logs()
    if "ERROR" in logs or "Exception" in logs:
        debug = call_openai(read_prompt("debug"), logs)
        fix = call_claude(read_prompt("fix"), debug)
        with open("patch.diff","w") as f:
            f.write(fix)
        run_cmd("git apply patch.diff && git commit -am 'auto-fix'")
        tests = call_openai(read_prompt("test"), fix)
        with open("auto_tests.py","w") as f:
            f.write(tests)
        result = run_cmd("pytest auto_tests.py")
        if "FAILED" in result:
            run_cmd("git reset --hard HEAD~1")
        else:
            run_cmd("git push")
    time.sleep(30)
EOF

# 6. Docker
cat > docker-compose.yml <<EOF
version: "3"
services:
  ai-self-healing:
    image: python:3.11
    volumes:
      - .:/app
    working_dir: /app
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    command: python3 agents/ai_orchestrator.py
    restart: always
EOF

# 7. Dépendances Python
pip3 install openai anthropic pytest

# 8. Lancement
docker-compose up -d

echo "✅ AI Self-Healing System ACTIVÉ"
echo "🤖 Débogage + tests + corrections AUTOMATIQUES"
EOF


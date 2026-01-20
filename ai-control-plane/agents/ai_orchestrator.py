import os, time, subprocess, json
from openai import OpenAI
import anthropic
import time

print("🤖 AI Self-Healing Orchestrator is running")

while True:
    time.sleep(30)

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

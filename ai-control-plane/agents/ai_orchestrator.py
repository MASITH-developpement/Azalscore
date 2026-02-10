import os, time, subprocess, json
from openai import OpenAI
import anthropic

print("🤖 AI Self-Healing Orchestrator is running")

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
    # Get logs from API and frontend containers
    api_logs = run_cmd("docker logs api --tail 100 2>&1")
    frontend_logs = run_cmd("docker logs azals_frontend --tail 50 2>&1")
    nginx_logs = run_cmd("docker logs azals_nginx --tail 50 2>&1")
    return f"=== API LOGS ===\n{api_logs}\n\n=== FRONTEND LOGS ===\n{frontend_logs}\n\n=== NGINX LOGS ===\n{nginx_logs}"

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
    try:
        print(f"[{time.strftime('%H:%M:%S')}] Checking logs...")
        logs = get_logs()
        print(f"[{time.strftime('%H:%M:%S')}] Got {len(logs)} chars of logs")

        # Detect various error patterns
        error_patterns = ["ERROR", "Exception", "Traceback", "403", "500", "502", "ValidationError", "CRITICAL"]
        has_error = any(pattern in logs for pattern in error_patterns)

        if has_error:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Errors detected! Starting auto-fix...")
            try:
                debug = call_openai(read_prompt("debug"), logs)
                print(f"[{time.strftime('%H:%M:%S')}] Debug analysis done")
                fix = call_claude(read_prompt("fix"), debug)
                print(f"[{time.strftime('%H:%M:%S')}] Fix generated")
                with open("patch.diff","w") as f:
                    f.write(fix)
                result = run_cmd("git apply patch.diff && git commit -am 'auto-fix'")
                print(f"[{time.strftime('%H:%M:%S')}] Patch applied: {result}")
                tests = call_openai(read_prompt("test"), fix)
                with open("auto_tests.py","w") as f:
                    f.write(tests)
                result = run_cmd("pytest auto_tests.py")
                if "FAILED" in result:
                    run_cmd("git reset --hard HEAD~1")
                    print(f"[{time.strftime('%H:%M:%S')}] ❌ Tests failed, rolled back")
                else:
                    run_cmd("git push")
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ Fix pushed!")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ Auto-fix failed: {e}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ✅ No errors detected")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Error in main loop: {e}")

    time.sleep(30)

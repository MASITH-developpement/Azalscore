"""Test pour générer des métriques IA"""
import os
import sys
sys.path.insert(0, '/home/ubuntu/azalscore')

os.environ.setdefault('DATABASE_URL', 'postgresql://azals:azals@localhost:5432/azals')

from app.core.metrics import (
    record_ai_inference,
    record_ai_tokens,
    record_guardian_decision,
    AI_SESSIONS_ACTIVE
)

# Simuler quelques appels Claude
for i in range(3):
    AI_SESSIONS_ACTIVE.inc()
    record_ai_inference("claude-sonnet-4", "reasoning", duration=1.5 + i*0.5, success=True)
    record_ai_tokens("claude-sonnet-4", input_tokens=500 + i*100, output_tokens=200 + i*50)
    record_guardian_decision("allowed", "low")
    AI_SESSIONS_ACTIVE.dec()

# Simuler quelques appels GPT
for i in range(2):
    AI_SESSIONS_ACTIVE.inc()
    record_ai_inference("gpt-4o", "structure", duration=0.8 + i*0.3, success=True)
    record_ai_tokens("gpt-4o", input_tokens=400 + i*80, output_tokens=150 + i*30)
    record_guardian_decision("allowed", "low")
    AI_SESSIONS_ACTIVE.dec()

print("✅ Métriques IA simulées avec succès")
print("   - 3 appels Claude")
print("   - 2 appels GPT-4")

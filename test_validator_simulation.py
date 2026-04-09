"""
Comprehensive test to simulate validator's task validation process.
Runs inference for all 3 tasks and checks if scores are strictly in (0, 1).
"""

import os
import sys
import subprocess
import re

# Set HF token for testing
os.environ["HF_TOKEN"] = "test_token"

# Test all three tasks
TASKS = [
    ("email_triage", "email_triage"),
    ("ticket_priority", "ticket_priority"),
    ("multi_turn_resolution", "multi_turn_resolution"),
]

print("\n" + "=" * 80)
print("COMPREHENSIVE VALIDATOR SIMULATION - Testing All 3 Tasks")
print("=" * 80)

for task_name, task_type in TASKS:
    print(f"\n[TASK] Testing {task_name} ({task_type})")
    print("-" * 80)
    
    # Set environment for this task
    env = os.environ.copy()
    env["CUSTOMER_SUPPORT_TASK"] = task_type
    env["CUSTOMER_SUPPORT_SEED"] = "42"
    
    # Create a minimal Python script to test the environment directly
    test_script = f"""
import os
os.environ["HF_TOKEN"] = "test_token"
os.environ["CUSTOMER_SUPPORT_TASK"] = "{task_type}"
os.environ["CUSTOMER_SUPPORT_SEED"] = "42"

from customer_support_env import CustomerSupportEnv, TaskType, Action, Category, Priority

# Task type mapping
TASK_MAP = {{
    "email_triage": TaskType.EASY,
    "ticket_priority": TaskType.MEDIUM,
    "multi_turn_resolution": TaskType.HARD,
}}

task_type = TASK_MAP["{task_type}"]
env = CustomerSupportEnv(task_type=task_type, seed=42)
obs = env.reset()

# Simulate 3 steps with reasonable actions
actions = []

if task_type == TaskType.EASY:
    # Use the correct category from the ticket
    actions = [
        Action(
            task_type=task_type,
            action_type="categorize",
            category=env.current_ticket.get("correct_category"),
        )
    ]
elif task_type == TaskType.MEDIUM:
    actions = [
        Action(
            task_type=task_type,
            action_type="assign_priority",
            priority=env.current_ticket.get("correct_priority"),
            suggested_next_step=env.current_ticket.get("correct_step"),
        )
    ]
else:  # HARD
    actions = [
        Action(
            task_type=task_type,
            action_type="respond",
            response_text="I understand your issue. Let me help you resolve this. Please try the following steps and let me know if it works.",
        )
    ]

rewards = []
for i, action in enumerate(actions, 1):
    obs, reward, done, info = env.step(action)
    rewards.append(reward.total_reward)
    
    # Verify all fields are strictly in (0, 1)
    fields = {{
        'total_reward': reward.total_reward,
        'correctness_score': reward.correctness_score,
        'efficiency_bonus': reward.efficiency_bonus,
        'customer_satisfaction': reward.customer_satisfaction,
    }}
    
    print(f"  Step {{i}}: ", end="")
    print(f"total={{reward.total_reward:.4f}}, ", end="")
    print(f"correct={{reward.correctness_score:.4f}}, ", end="")
    print(f"efficiency={{reward.efficiency_bonus:.4f}}, ", end="")
    print(f"satisfaction={{reward.customer_satisfaction:.4f}}")
    
    # Check bounds
    for field_name, field_value in fields.items():
        if field_value <= 0.0 or field_value >= 1.0:
            print(f"    ❌ ERROR: {{field_name}}={{field_value}} is NOT in (0, 1)!")
            sys.exit(1)

print(f"  ✅ All rewards for {task_type} are strictly in (0, 1)")
"""
    
    # Run the test script
    result = subprocess.run(
        ["python", "-c", test_script],
        cwd="d:\\Vibe_Coding\\OpenEnv_T-1",
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"❌ FAILED: {task_name}")
        sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL TASKS PASSED - All 3 tasks have scores strictly in (0, 1)")
print("=" * 80)

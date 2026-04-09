"""
Test all graders directly without subprocess complexity.
"""

import os

os.environ["HF_TOKEN"] = "test_token"

from customer_support_env import (
    CustomerSupportEnv,
    TaskType,
    Action,
    Category,
    Priority,
)

print("\n" + "=" * 80)
print("TESTING ALL 3 TASK GRADERS")
print("=" * 80)

all_pass = True

# Test 1: EASY
print("\n[1] EMAIL TRIAGE (EASY)")
print("-" * 80)
for seed in [42, 100, 200]:
    env = CustomerSupportEnv(task_type=TaskType.EASY, seed=seed)
    obs = env.reset()
    
    action = Action(
        task_type=TaskType.EASY,
        action_type="categorize",
        category=env.current_ticket.get("correct_category"),
    )
    obs, reward, done, info = env.step(action)
    
    print(f"Seed {seed}: total={reward.total_reward:.4f}, correct={reward.correctness_score:.4f}, bonus={reward.efficiency_bonus:.4f}, satisfaction={reward.customer_satisfaction:.4f}")
    
    # Check all fields
    for field_name, field_val in [
        ("total_reward", reward.total_reward),
        ("correctness_score", reward.correctness_score),
        ("efficiency_bonus", reward.efficiency_bonus),
        ("customer_satisfaction", reward.customer_satisfaction),
    ]:
        if not (0 < field_val < 1):
            print(f"  ❌ {field_name} = {field_val} is OUT OF RANGE!")
            all_pass = False

# Test 2: MEDIUM
print("\n[2] TICKET PRIORITY (MEDIUM)")
print("-" * 80)
for seed in [42, 100, 200]:
    env = CustomerSupportEnv(task_type=TaskType.MEDIUM, seed=seed)
    obs = env.reset()
    
    action = Action(
        task_type=TaskType.MEDIUM,
        action_type="assign_priority",
        priority=env.current_ticket.get("correct_priority"),
        suggested_next_step=env.current_ticket.get("correct_step"),
    )
    obs, reward, done, info = env.step(action)
    
    print(f"Seed {seed}: total={reward.total_reward:.4f}, correct={reward.correctness_score:.4f}, bonus={reward.efficiency_bonus:.4f}, satisfaction={reward.customer_satisfaction:.4f}")
    
    # Check all fields
    for field_name, field_val in [
        ("total_reward", reward.total_reward),
        ("correctness_score", reward.correctness_score),
        ("efficiency_bonus", reward.efficiency_bonus),
        ("customer_satisfaction", reward.customer_satisfaction),
    ]:
        if not (0 < field_val < 1):
            print(f"  ❌ {field_name} = {field_val} is OUT OF RANGE!")
            all_pass = False

# Test 3: HARD
print("\n[3] MULTI-TURN RESOLUTION (HARD)")
print("-" * 80)
for seed in [42, 100, 200]:
    env = CustomerSupportEnv(task_type=TaskType.HARD, seed=seed)
    obs = env.reset()
    
    action = Action(
        task_type=TaskType.HARD,
        action_type="respond",
        response_text="I understand your issue. Let me help you troubleshoot. Please try restarting and verify the settings work.",
    )
    obs, reward, done, info = env.step(action)
    
    print(f"Seed {seed}: total={reward.total_reward:.4f}, correct={reward.correctness_score:.4f}, bonus={reward.efficiency_bonus:.4f}, satisfaction={reward.customer_satisfaction:.4f}")
    
    # Check all fields
    for field_name, field_val in [
        ("total_reward", reward.total_reward),
        ("correctness_score", reward.correctness_score),
        ("efficiency_bonus", reward.efficiency_bonus),
        ("customer_satisfaction", reward.customer_satisfaction),
    ]:
        if not (0 < field_val < 1):
            print(f"  ❌ {field_name} = {field_val} is OUT OF RANGE!")
            all_pass = False

print("\n" + "=" * 80)
if all_pass:
    print("✅ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 80)

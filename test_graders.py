"""Test script to verify all Reward fields are strictly between 0 and 1."""

import os
import sys

# Set API key to avoid errors during initialization
os.environ["HF_TOKEN"] = "test_token_12345"

from customer_support_env import (
    CustomerSupportEnv,
    TaskType,
    Action,
    Category,
    Priority,
)


def test_graders():
    """Test all three graders to verify reward scores are strictly (0, 1)."""
    
    print("\n" + "=" * 70)
    print("TESTING ALL GRADERS - Verifying scores are strictly (0, 1)")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Email Triage (EASY)
    print("\n[TEST 1] Email Triage (EASY) Grader")
    print("-" * 70)
    env_easy = CustomerSupportEnv(task_type=TaskType.EASY, seed=42)
    obs = env_easy.reset()
    
    # Test valid action
    action_correct = Action(
        task_type=TaskType.EASY,
        action_type="categorize",
        category=env_easy.current_ticket.get("correct_category"),
    )
    obs, reward, done, info = env_easy.step(action_correct)
    
    print(f"  Correct categorization:")
    print(f"    - total_reward: {reward.total_reward:.4f}")
    print(f"    - correctness_score: {reward.correctness_score:.4f}")
    print(f"    - efficiency_bonus: {reward.efficiency_bonus:.4f}")
    print(f"    - customer_satisfaction: {reward.customer_satisfaction:.4f}")
    
    # Check all fields are in (0, 1)
    fields_easy = [
        reward.total_reward,
        reward.correctness_score,
        reward.efficiency_bonus,
        reward.customer_satisfaction,
    ]
    all_valid_easy = all(0 < f < 1 for f in fields_easy)
    test_results.append(("EASY - Correct", all_valid_easy, fields_easy))
    
    # Test invalid action
    env_easy2 = CustomerSupportEnv(task_type=TaskType.EASY, seed=42)
    obs = env_easy2.reset()
    action_invalid = Action(
        task_type=TaskType.EASY,
        action_type="categorize",
        category=None,  # Invalid
    )
    obs, reward, done, info = env_easy2.step(action_invalid)
    
    print(f"\n  Invalid action:")
    print(f"    - total_reward: {reward.total_reward:.4f}")
    print(f"    - correctness_score: {reward.correctness_score:.4f}")
    print(f"    - efficiency_bonus: {reward.efficiency_bonus:.4f}")
    print(f"    - customer_satisfaction: {reward.customer_satisfaction:.4f}")
    
    fields_easy_invalid = [
        reward.total_reward,
        reward.correctness_score,
        reward.efficiency_bonus,
        reward.customer_satisfaction,
    ]
    all_valid_easy_invalid = all(0 < f < 1 for f in fields_easy_invalid)
    test_results.append(("EASY - Invalid", all_valid_easy_invalid, fields_easy_invalid))
    
    # Test 2: Ticket Priority (MEDIUM)
    print("\n[TEST 2] Ticket Priority (MEDIUM) Grader")
    print("-" * 70)
    env_medium = CustomerSupportEnv(task_type=TaskType.MEDIUM, seed=42)
    obs = env_medium.reset()
    
    # Test valid action
    action_correct = Action(
        task_type=TaskType.MEDIUM,
        action_type="assign_priority",
        priority=env_medium.current_ticket.get("correct_priority"),
        suggested_next_step=env_medium.current_ticket.get("correct_step"),
    )
    obs, reward, done, info = env_medium.step(action_correct)
    
    print(f"  Correct priority assignment:")
    print(f"    - total_reward: {reward.total_reward:.4f}")
    print(f"    - correctness_score: {reward.correctness_score:.4f}")
    print(f"    - efficiency_bonus: {reward.efficiency_bonus:.4f}")
    print(f"    - customer_satisfaction: {reward.customer_satisfaction:.4f}")
    
    fields_medium = [
        reward.total_reward,
        reward.correctness_score,
        reward.efficiency_bonus,
        reward.customer_satisfaction,
    ]
    all_valid_medium = all(0 < f < 1 for f in fields_medium)
    test_results.append(("MEDIUM - Correct", all_valid_medium, fields_medium))
    
    # Test invalid action
    env_medium2 = CustomerSupportEnv(task_type=TaskType.MEDIUM, seed=42)
    obs = env_medium2.reset()
    action_invalid = Action(
        task_type=TaskType.MEDIUM,
        action_type="assign_priority",
        priority=None,  # Invalid
        suggested_next_step=None,
    )
    obs, reward, done, info = env_medium2.step(action_invalid)
    
    print(f"\n  Invalid action:")
    print(f"    - total_reward: {reward.total_reward:.4f}")
    print(f"    - correctness_score: {reward.correctness_score:.4f}")
    print(f"    - efficiency_bonus: {reward.efficiency_bonus:.4f}")
    print(f"    - customer_satisfaction: {reward.customer_satisfaction:.4f}")
    
    fields_medium_invalid = [
        reward.total_reward,
        reward.correctness_score,
        reward.efficiency_bonus,
        reward.customer_satisfaction,
    ]
    all_valid_medium_invalid = all(0 < f < 1 for f in fields_medium_invalid)
    test_results.append(("MEDIUM - Invalid", all_valid_medium_invalid, fields_medium_invalid))
    
    # Test 3: Multi-turn Resolution (HARD)
    print("\n[TEST 3] Multi-turn Resolution (HARD) Grader")
    print("-" * 70)
    env_hard = CustomerSupportEnv(task_type=TaskType.HARD, seed=42)
    obs = env_hard.reset()
    
    # Test valid action
    action_correct = Action(
        task_type=TaskType.HARD,
        action_type="respond",
        response_text="I understand your issue. Let me help you troubleshoot this problem. Please try restarting your device.",
    )
    obs, reward, done, info = env_hard.step(action_correct)
    
    print(f"  Good response:")
    print(f"    - total_reward: {reward.total_reward:.4f}")
    print(f"    - correctness_score: {reward.correctness_score:.4f}")
    print(f"    - efficiency_bonus: {reward.efficiency_bonus:.4f}")
    print(f"    - customer_satisfaction: {reward.customer_satisfaction:.4f}")
    
    fields_hard = [
        reward.total_reward,
        reward.correctness_score,
        reward.efficiency_bonus,
        reward.customer_satisfaction,
    ]
    all_valid_hard = all(0 < f < 1 for f in fields_hard)
    test_results.append(("HARD - Good", all_valid_hard, fields_hard))
    
    # Test invalid action
    env_hard2 = CustomerSupportEnv(task_type=TaskType.HARD, seed=42)
    obs = env_hard2.reset()
    action_invalid = Action(
        task_type=TaskType.HARD,
        action_type="respond",
        response_text="",  # Empty response
    )
    obs, reward, done, info = env_hard2.step(action_invalid)
    
    print(f"\n  Invalid action:")
    print(f"    - total_reward: {reward.total_reward:.4f}")
    print(f"    - correctness_score: {reward.correctness_score:.4f}")
    print(f"    - efficiency_bonus: {reward.efficiency_bonus:.4f}")
    print(f"    - customer_satisfaction: {reward.customer_satisfaction:.4f}")
    
    fields_hard_invalid = [
        reward.total_reward,
        reward.correctness_score,
        reward.efficiency_bonus,
        reward.customer_satisfaction,
    ]
    all_valid_hard_invalid = all(0 < f < 1 for f in fields_hard_invalid)
    test_results.append(("HARD - Invalid", all_valid_hard_invalid, fields_hard_invalid))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    all_pass = True
    for test_name, passed, fields in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            print(f"    Fields: {[f'{f:.4f}' for f in fields]}")
            for i, f in enumerate(fields):
                if f <= 0 or f >= 1:
                    print(f"    ⚠️ Field {i} out of range: {f:.4f}")
            all_pass = False
    
    print("=" * 70)
    if all_pass:
        print("✅ ALL TESTS PASSED - All scores strictly in (0, 1)")
        return True
    else:
        print("❌ SOME TESTS FAILED - Fix graders")
        return False


if __name__ == "__main__":
    success = test_graders()
    sys.exit(0 if success else 1)

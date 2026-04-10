"""
Demonstration script showing the full environment working
both locally without API credentials AND with LLM inference
"""
import os
from typing import Optional

from openai import OpenAI

from customer_support_env import (
    Action,
    Category,
    CustomerSupportEnv,
    Priority,
    TaskType,
)

# Configuration from environment
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")


def demonstrate_easy_task():
    """Demonstrate email triage task."""
    print("\n" + "="*60)
    print("EASY TASK: EMAIL TRIAGE")
    print("="*60)
    
    env = CustomerSupportEnv(TaskType.EASY, seed=42)
    obs = env.reset()
    
    print(f"\nTicket ID: {obs.ticket_id}")
    print(f"Sentiment: {obs.customer_sentiment}")
    print(f"Message: {obs.customer_message}\n")
    
    # Simulate correct categorization
    action = Action(
        task_type=TaskType.EASY,
        action_type="categorize",
        category=Category.BILLING
    )
    
    obs, reward, done, info = env.step(action)
    print(f"Agent Action: Categorized as '{action.category.value}'")
    print(f"Reward: {reward.total_reward:.3f}")
    print(f"Details: {reward.details}")
    
    return reward.total_reward


def demonstrate_medium_task():
    """Demonstrate ticket priority assignment task."""
    print("\n" + "="*60)
    print("MEDIUM TASK: TICKET PRIORITY ASSIGNMENT")
    print("="*60)
    
    env = CustomerSupportEnv(TaskType.MEDIUM, seed=42)
    obs = env.reset()
    
    print(f"\nTicket ID: {obs.ticket_id}")
    print(f"Context: {obs.previous_context}")
    print(f"Sentiment: {obs.customer_sentiment}")
    print(f"Message: {obs.customer_message}\n")
    
    # Simulate correct priority assignment
    action = Action(
        task_type=TaskType.MEDIUM,
        action_type="assign_priority",
        priority=Priority.URGENT,
        suggested_next_step="escalate_to_engineering"
    )
    
    obs, reward, done, info = env.step(action)
    print(f"Agent Action:")
    print(f"  Priority: {action.priority.value}")
    print(f"  Next Step: {action.suggested_next_step}")
    print(f"Reward: {reward.total_reward:.3f}")
    print(f"Details: {reward.details}")
    
    return reward.total_reward


def demonstrate_hard_task():
    """Demonstrate multi-turn resolution task."""
    print("\n" + "="*60)
    print("HARD TASK: MULTI-TURN RESOLUTION")
    print("="*60)
    
    env = CustomerSupportEnv(TaskType.HARD, seed=42)
    obs = env.reset()
    
    print(f"\nTicket ID: {obs.ticket_id}")
    print(f"Step {obs.step_number}: Customer message:")
    print(f"  {obs.customer_message}")
    print(f"  Sentiment: {obs.customer_sentiment}\n")
    
    # Simulate substantive, empathetic response
    response = """I understand how frustrating this must be. Let's troubleshoot your API key issue step by step. 
First, can you try regenerating your API key from the dashboard and let me know if that resolves the 401 errors?"""
    
    action = Action(
        task_type=TaskType.HARD,
        action_type="respond",
        response_text=response
    )
    
    obs, reward, done, info = env.step(action)
    print(f"Agent Response:\n  {response}\n")
    print(f"Reward: {reward.total_reward:.3f}")
    print(f"Details: {reward.details}")
    
    # Continue multi-turn
    if not done and obs.customer_message != "Problem resolved.":
        print(f"\nStep {obs.step_number}: Customer followup:")
        print(f"  {obs.customer_message}")
        print(f"  Sentiment: {obs.customer_sentiment}\n")
        
        response2 = """Thanks for trying that. If regenerating the key didn't work, 
let me escalate this to our engineering team. They'll investigate the root cause and get back to you within 2 hours."""
        
        action2 = Action(
            task_type=TaskType.HARD,
            action_type="respond",
            response_text=response2
        )
        
        obs, reward2, done, info = env.step(action2)
        print(f"Agent Response:\n  {response2}\n")
        print(f"Reward: {reward2.total_reward:.3f}")
        
        return reward.total_reward + reward2.total_reward
    
    return reward.total_reward


def demonstrate_llm_inference():
    """Demonstrate LLM-based inference on all three tasks."""
    if not API_KEY:
        print("\n⚠️  API_KEY not set. Skipping LLM-based demonstrations.")
        print("To enable: export HF_TOKEN='your-api-key'")
        return None
    
    print("\n" + "="*60)
    print("LLM-BASED INFERENCE DEMONSTRATIONS")
    print("="*60)
    print(f"\nUsing model: {MODEL_NAME}")
    print(f"API endpoint: {API_BASE_URL}\n")
    
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE_URL
        )
        
        # Test connection
        print("Testing API connection...", end=" ", flush=True)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10,
        )
        print("✓ Connected\n")
        
    except Exception as e:
        print(f"✗ API Error: {e}")
        return None
    
    scores = {}
    
    # Easy Task - Email Triage
    print("EASY TASK: EMAIL TRIAGE (LLM-based)")
    print("-" * 40)
    try:
        env = CustomerSupportEnv(TaskType.EASY, seed=123)
        obs = env.reset()
        
        print(f"Ticket: {obs.ticket_id}")
        print(f"Message: {obs.customer_message[:60]}...")
        print(f"Sentiment: {obs.customer_sentiment}\n")
        
        # Get LLM categorization
        prompt = f"Categorize this support email. Only respond with ONE of: billing, technical, account, shipping.\n\nEmail: {obs.customer_message}"
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
        )
        category_text = response.choices[0].message.content.lower().strip()
        
        # Parse category
        for cat in Category:
            if cat.value in category_text:
                action = Action(
                    task_type=TaskType.EASY,
                    action_type="categorize",
                    category=cat,
                )
                break
        else:
            action = Action(
                task_type=TaskType.EASY,
                action_type="categorize",
                category=Category.OTHER,
            )
        
        obs, reward, done, info = env.step(action)
        print(f"LLM Categorized as: {action.category.value}")
        print(f"Reward: {reward.total_reward:.3f}")
        scores['easy'] = reward.total_reward
        print()
        
    except Exception as e:
        print(f"Error: {e}\n")
        scores['easy'] = 0.0
    
    # Medium Task - Priority Assignment
    print("MEDIUM TASK: PRIORITY ASSIGNMENT (LLM-based)")
    print("-" * 40)
    try:
        env = CustomerSupportEnv(TaskType.MEDIUM, seed=123)
        obs = env.reset()
        
        print(f"Ticket: {obs.ticket_id}")
        print(f"Message: {obs.customer_message[:60]}...")
        print(f"Sentiment: {obs.customer_sentiment}\n")
        
        # Get LLM priority
        prompt = f"""Assign priority to this support ticket. Respond in this format:
PRIORITY: [CRITICAL, URGENT, HIGH, MEDIUM, or LOW]
NEXT_STEP: [escalate_to_engineering, schedule_callback, or provide_workaround]

Ticket: {obs.customer_message}"""
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        response_text = response.choices[0].message.content.upper()
        
        # Parse response
        priority = Priority.MEDIUM
        next_step = "provide_workaround"
        
        for prio in Priority:
            if prio.value.upper() in response_text:
                priority = prio
                break
        
        if "escalate" in response_text:
            next_step = "escalate_to_engineering"
        elif "callback" in response_text:
            next_step = "schedule_callback"
        
        action = Action(
            task_type=TaskType.MEDIUM,
            action_type="assign_priority",
            priority=priority,
            suggested_next_step=next_step,
        )
        
        obs, reward, done, info = env.step(action)
        print(f"LLM Assigned: Priority={action.priority.value}, Next Step={action.suggested_next_step}")
        print(f"Reward: {reward.total_reward:.3f}")
        scores['medium'] = reward.total_reward
        print()
        
    except Exception as e:
        print(f"Error: {e}\n")
        scores['medium'] = 0.0
    
    # Hard Task - Multi-turn Resolution
    print("HARD TASK: MULTI-TURN RESOLUTION (LLM-based)")
    print("-" * 40)
    try:
        env = CustomerSupportEnv(TaskType.HARD, seed=123)
        obs = env.reset()
        
        print(f"Ticket: {obs.ticket_id}")
        print(f"Customer: {obs.customer_message[:60]}...\n")
        
        # Get LLM response
        prompt = f"""You are a professional support agent. Respond to this customer support message with empathy and concrete next steps.
Keep response concise (2-3 sentences).

Customer: {obs.customer_message}"""
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        response_text = response.choices[0].message.content
        
        action = Action(
            task_type=TaskType.HARD,
            action_type="respond",
            response_text=response_text,
        )
        
        obs, reward, done, info = env.step(action)
        print(f"LLM Response: {response_text[:80]}...")
        print(f"Reward: {reward.total_reward:.3f}")
        scores['hard'] = reward.total_reward
        print()
        
    except Exception as e:
        print(f"Error: {e}\n")
        scores['hard'] = 0.0
    
    return scores


def main():
    """Run demonstrations of all three tasks."""
    print("\n" + "="*60)
    print("AI CUSTOMER SUPPORT RESOLUTION SYSTEM - DEMONSTRATION")
    print("="*60)
    print("\n📍 PART 1: LOCAL DEMONSTRATIONS (no API needed)")
    print("="*60)
    print("\nThe environment includes three tasks of increasing difficulty:\n")
    
    # Run demonstrations
    score_easy = demonstrate_easy_task()
    score_medium = demonstrate_medium_task()
    score_hard = demonstrate_hard_task()
    
    # Summary - Local
    print("\n" + "="*60)
    print("PART 1: LOCAL RESULTS")
    print("="*60)
    print(f"\nEasy Task (Email Triage) Score: {score_easy:.3f}")
    print(f"Medium Task (Priority Assignment) Score: {score_medium:.3f}")
    print(f"Hard Task (Multi-turn Resolution) Score: {score_hard:.3f}")
    local_avg = (score_easy + score_medium + score_hard) / 3
    print(f"\nLocal Average Score: {local_avg:.3f}")
    
    # LLM-based Inference
    print("\n" + "="*60)
    print("📍 PART 2: LLM-BASED INFERENCE (with API)")
    print("="*60)
    llm_scores = demonstrate_llm_inference()
    
    # Summary - LLM
    if llm_scores:
        print("\n" + "="*60)
        print("PART 2: LLM-BASED RESULTS")
        print("="*60)
        print(f"\nEasy Task (Email Triage) Score: {llm_scores.get('easy', 0):.3f}")
        print(f"Medium Task (Priority Assignment) Score: {llm_scores.get('medium', 0):.3f}")
        print(f"Hard Task (Multi-turn Resolution) Score: {llm_scores.get('hard', 0):.3f}")
        llm_avg = sum(llm_scores.values()) / len(llm_scores) if llm_scores else 0
        print(f"\nLLM Average Score: {llm_avg:.3f}")
        
        print("\n" + "="*60)
        print("OVERALL SUMMARY")
        print("="*60)
        print(f"\nLocal Average: {local_avg:.3f}")
        print(f"LLM Average: {llm_avg:.3f}")
    
    print("\n✓ All demonstrations completed successfully!")
    print("\nTo run with actual LLM inference, set environment variables:")
    print("  export HF_TOKEN='your-api-key'")
    print("  export API_BASE_URL='https://router.huggingface.co/v1'")
    print("  export MODEL_NAME='Qwen/Qwen2.5-72B-Instruct'")
    print("  python Inference.py")


if __name__ == "__main__":
    main()

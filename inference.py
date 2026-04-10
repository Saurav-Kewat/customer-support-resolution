"""
Inference Script for AI Customer Support Resolution System

MANDATORY REQUIREMENTS:
- Named: inference.py (lowercase)
- Location: Repository root
- Stdout format: [START], [STEP], [END]
- Uses OpenAI Client for LLM calls
- Environment variables: HF_TOKEN, API_BASE_URL, MODEL_NAME

STDOUT FORMAT:
[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
from typing import List, Optional

from openai import OpenAI

from customer_support_env import (
    Action,
    Category,
    CustomerSupportEnv,
    Priority,
    TaskType,
)

# Configuration from environment - MUST use injected env vars for LiteLLM proxy
API_KEY = os.environ.get("API_KEY") or os.environ.get("HF_TOKEN", "")
API_BASE_URL = os.environ.get("API_BASE_URL", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# Task and environment configuration
TASK_NAME = os.getenv("CUSTOMER_SUPPORT_TASK", "email_triage")
BENCHMARK = "customer_support_resolution"
MAX_STEPS = 8
TEMPERATURE = 0.7
MAX_TOKENS = 200
SEED = int(os.getenv("CUSTOMER_SUPPORT_SEED", "42"))

# Task type mapping
TASK_MAP = {
    "email_triage": TaskType.EASY,
    "ticket_priority": TaskType.MEDIUM,
    "multi_turn_resolution": TaskType.HARD,
}

# System prompts for each task
SYSTEM_PROMPTS = {
    TaskType.EASY: textwrap.dedent("""
        You are a customer support AI tasked with email triage.
        Your job is to quickly and accurately categorize incoming customer emails.
        
        CATEGORIES:
        - billing: Questions about charges, payments, subscriptions, invoices
        - technical: Technical issues, bug reports, how-to questions
        - account: Account access, password resets, profile issues
        - feedback: Praise, feature requests, general feedback
        - other: Anything else
        
        Respond with ONLY the category name (billing, technical, account, feedback, or other).
        Do not explain, just output the category.
    """).strip(),
    
    TaskType.MEDIUM: textwrap.dedent("""
        You are a customer support triage manager.
        Your job is to assess support tickets and recommend priority levels and next steps.
        
        PRIORITY LEVELS:
        - urgent: Critical system outages affecting all users
        - high: Data loss, payment failures, or widespread issues
        - medium: Important functional issues affecting individual users
        - low: General questions, documentation requests
        
        NEXT STEPS (choose most appropriate):
        - escalate_to_engineering: For technical/system issues
        - process_payment_retry: For billing/payment failures
        - send_documentation: For questions answerable by docs
        - investigate_data_loss: For data integrity concerns
        - offer_extension: For subscription/plan issues
        
        Think through the issue and respond in this format:
        PRIORITY: [urgent|high|medium|low]
        NEXT_STEP: [option]
        
        Be concise and professional.
    """).strip(),
    
    TaskType.HARD: textwrap.dedent("""
        You are an experienced customer support representative handling complex issues.
        Your job is to provide empathetic, helpful responses that move toward resolution.
        
        Guidelines:
        1. Start by acknowledging the customer's concern
        2. Ask clarifying questions if needed
        3. Provide concrete next steps or solutions
        4. Offer alternatives if the first solution doesn't work
        5. End with clear action items
        
        Be empathetic, professional, and solution-focused.
        Keep responses concise but substantive (2-3 sentences minimum).
        If an issue seems complex or data-related, suggest escalation to engineering.
    """).strip(),
}


def log_start(task: str, env: str, model: str) -> None:
    """Log episode start."""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log step execution."""
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Log episode end."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def build_user_prompt(step: int, observation) -> str:
    """Build the user prompt based on task type."""
    base = f"Step {step}/{MAX_STEPS}\n\n"
    base += f"Ticket ID: {observation.ticket_id}\n"
    base += f"Customer Message: {observation.customer_message}\n"
    
    if observation.previous_context:
        base += f"Context: {observation.previous_context}\n"
    
    base += f"Sentiment: {observation.customer_sentiment}\n\n"
    
    task_type = TASK_MAP[TASK_NAME]
    if task_type == TaskType.EASY:
        base += "Task: Categorize this email. Respond with ONLY the category name."
    elif task_type == TaskType.MEDIUM:
        base += "Task: Assign priority and suggest next steps. Use the format:\nPRIORITY: [level]\nNEXT_STEP: [action]"
    else:  # HARD
        base += "Task: Provide a helpful response to move the ticket toward resolution."
    
    return base


def parse_agent_response(response_text: str, task_type: TaskType) -> Optional[Action]:
    """Parse LLM response into an Action."""
    response_text = response_text.strip()
    
    try:
        if task_type == TaskType.EASY:
            # Parse category
            category_str = response_text.lower().strip()
            for cat in Category:
                if cat.value in category_str:
                    return Action(
                        task_type=task_type,
                        action_type="categorize",
                        category=cat,
                    )
            # Default to other if not recognized
            return Action(
                task_type=task_type,
                action_type="categorize",
                category=Category.OTHER,
            )
        
        elif task_type == TaskType.MEDIUM:
            # Parse priority and next step
            lines = response_text.split("\n")
            priority = None
            next_step = None
            
            for line in lines:
                if "PRIORITY:" in line.upper():
                    priority_str = line.split(":")[-1].strip().lower()
                    for p in Priority:
                        if p.value in priority_str:
                            priority = p
                            break
                elif "NEXT_STEP:" in line.upper():
                    next_step = line.split(":")[-1].strip()
            
            if priority and next_step:
                return Action(
                    task_type=task_type,
                    action_type="assign_priority",
                    priority=priority,
                    suggested_next_step=next_step,
                )
        
        else:  # HARD
            # Use full response as the agent's reply
            return Action(
                task_type=task_type,
                action_type="respond",
                response_text=response_text,
            )
    
    except Exception as e:
        print(f"[DEBUG] Failed to parse response: {e}", flush=True)
        return None
    
    return None


def main() -> None:
    """Main entry point - runs inference episode with proper stdout logging."""
    
    # Check if API key and base URL are available
    if not API_KEY:
        print("[WARN] API_KEY not set - skipping inference (will be injected by validator)", flush=True)
        return
    
    if not API_BASE_URL:
        print("[WARN] API_BASE_URL not set - skipping inference (will be injected by validator)", flush=True)
        return
    
    # Initialize OpenAI client with injected proxy URL and API key
    try:
        client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
    except Exception as e:
        print(f"[ERROR] Failed to initialize OpenAI client: {e}", flush=True)
        sys.exit(1)
    
    # Get task type
    if TASK_NAME not in TASK_MAP:
        print(f"[ERROR] Unknown task: {TASK_NAME}", flush=True)
        sys.exit(1)
    
    task_type = TASK_MAP[TASK_NAME]
    
    # Initialize environment
    try:
        env = CustomerSupportEnv(task_type=task_type, seed=SEED)
    except Exception as e:
        print(f"[ERROR] Failed to initialize environment: {e}", flush=True)
        sys.exit(1)
    
    # Run episode
    total_reward = 0.0
    all_rewards = []
    steps_taken = 0
    last_error = None
    
    log_start(TASK_NAME, BENCHMARK, MODEL_NAME)
    
    try:
        obs = env.reset()
        
        for step in range(1, MAX_STEPS + 1):
            try:
                # Build prompt
                user_prompt = build_user_prompt(step, obs)
                system_prompt = SYSTEM_PROMPTS[task_type]
                
                # Call LLM
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                )
                
                response_text = response.choices[0].message.content
                
                # Parse response into action
                action = parse_agent_response(response_text, task_type)
                if not action:
                    raise ValueError("Failed to parse agent response")
                
                # Execute action
                obs, reward, done, info = env.step(action)
                
                # Log step (REQUIRED FORMAT)
                action_str = response_text.replace("\n", " ")[:100]  # Truncate for logging
                log_step(step, action_str, reward.total_reward, done, last_error)
                
                total_reward += reward.total_reward
                all_rewards.append(reward.total_reward)
                steps_taken = step
                last_error = None
                
                if done:
                    break
            
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                log_step(step, "<error>", 0.01, True, error_msg)
                break
        
        # Calculate success
        success = steps_taken > 0 and total_reward > 0.1
        
        # Log end (REQUIRED FORMAT)
        log_end(success, steps_taken, total_reward, all_rewards)
    
    except Exception as e:
        print(f"[ERROR] Episode failed: {e}", flush=True)
        log_end(False, 0, 0.01, [0.01])


if __name__ == "__main__":
    main()

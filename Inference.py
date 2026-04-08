"""
Inference Script for AI Customer Support Resolution System

This script demonstrates the environment by running an AI agent (via OpenAI API)
through customer support resolution tasks.

Environment Variables (REQUIRED):
  - HF_TOKEN or API_KEY: Your API key for the LLM
  - API_BASE_URL: The API endpoint (default: https://router.huggingface.co/v1)
  - MODEL_NAME: The model to use (default: Qwen/Qwen2.5-72B-Instruct)

Optional:
  - CUSTOMER_SUPPORT_TASK: Task type (email_triage, ticket_priority, multi_turn_resolution)
  - CUSTOMER_SUPPORT_SEED: Random seed for reproducibility
  - MAX_EPISODES: Number of episodes to run (default: 1, preserves credits)

Set MAX_EPISODES for more runs:
  export MAX_EPISODES=3  # Run 3 episodes then exit
"""

import os
import textwrap
from typing import List, Optional

import httpx
from openai import OpenAI

from customer_support_env import (
    Action,
    Category,
    CustomerSupportEnv,
    Priority,
    Reward,
    TaskType,
)

# Configuration from environment
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# Task and environment configuration
TASK_NAME = os.getenv("CUSTOMER_SUPPORT_TASK", "email_triage")
BENCHMARK = "customer_support_resolution"
MAX_STEPS = 8
TEMPERATURE = 0.7
MAX_TOKENS = 200
SEED = int(os.getenv("CUSTOMER_SUPPORT_SEED", "42"))

# Map string task names to TaskType enum
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


class InferenceRunner:
    """Runs inference on the customer support environment."""
    
    def __init__(self):
        """Initialize the runner with OpenAI client."""
        if not API_KEY:
            raise ValueError("API_KEY or HF_TOKEN environment variable must be set")
        
        # Create custom http_client to avoid proxy issues
        http_client = httpx.Client(
            timeout=30.0,
            verify=True,
        )
        
        self.client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE_URL,
            http_client=http_client
        )
        self.model = MODEL_NAME
        
        # Select task
        if TASK_NAME not in TASK_MAP:
            raise ValueError(f"Unknown task: {TASK_NAME}. Must be one of {list(TASK_MAP.keys())}")
        
        self.task_type = TASK_MAP[TASK_NAME]
        self.env = CustomerSupportEnv(task_type=self.task_type, seed=SEED)
    
    def log_start(self, task: str, env: str, model: str) -> None:
        """Log episode start."""
        print(f"[START] task={task} env={env} model={model}", flush=True)
    
    def log_step(
        self, step: int, action: str, reward: float, done: bool, error: Optional[str]
    ) -> None:
        """Log step execution."""
        error_val = error if error else "null"
        done_val = str(done).lower()
        print(
            f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
            flush=True,
        )
    
    def log_end(self, success: bool, steps: int, score: float, rewards: List[float]) -> None:
        """Log episode end."""
        rewards_str = ",".join(f"{r:.2f}" for r in rewards)
        print(
            f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
            flush=True,
        )
    
    def build_user_prompt(self, step: int, observation) -> str:
        """Build the user prompt based on task type."""
        base = f"Step {step}/{MAX_STEPS}\n\n"
        base += f"Ticket ID: {observation.ticket_id}\n"
        base += f"Customer Message: {observation.customer_message}\n"
        
        if observation.previous_context:
            base += f"Context: {observation.previous_context}\n"
        
        base += f"Sentiment: {observation.customer_sentiment}\n\n"
        
        if self.task_type == TaskType.EASY:
            base += "Task: Categorize this email. Respond with ONLY the category name."
        elif self.task_type == TaskType.MEDIUM:
            base += "Task: Assign priority and suggest next steps. Use the format:\nPRIORITY: [level]\nNEXT_STEP: [action]"
        else:  # HARD
            base += "Task: Provide a helpful response to move the ticket toward resolution."
        
        return base
    
    def parse_agent_response(self, response_text: str) -> Optional[Action]:
        """Parse LLM response into an Action."""
        response_text = response_text.strip()
        
        try:
            if self.task_type == TaskType.EASY:
                # Parse category
                category_str = response_text.lower().strip()
                for cat in Category:
                    if cat.value in category_str:
                        return Action(
                            task_type=self.task_type,
                            action_type="categorize",
                            category=cat,
                        )
                # Default to other if not recognized
                return Action(
                    task_type=self.task_type,
                    action_type="categorize",
                    category=Category.OTHER,
                )
            
            elif self.task_type == TaskType.MEDIUM:
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
                        task_type=self.task_type,
                        action_type="assign_priority",
                        priority=priority,
                        suggested_next_step=next_step,
                    )
            
            else:  # HARD
                # Use full response as the agent's reply
                return Action(
                    task_type=self.task_type,
                    action_type="respond",
                    response_text=response_text,
                )
        
        except Exception as e:
            print(f"[ERROR] Failed to parse response: {e}", flush=True)
            return None
    
    def run_episode(self) -> tuple:
        """Run a single episode."""
        # Initialize
        obs = self.env.reset()
        self.log_start(self.task_type.value, BENCHMARK, self.model)
        
        total_reward = 0.0
        all_rewards = []
        steps_taken = 0
        last_error = None
        
        for step in range(1, MAX_STEPS + 1):
            # Get action from LLM
            try:
                user_prompt = self.build_user_prompt(step, obs)
                system_prompt = SYSTEM_PROMPTS[self.task_type]
                
                # Call LLM
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                )
                
                response_text = response.choices[0].message.content
                
                # Parse response into action
                action = self.parse_agent_response(response_text)
                if not action:
                    raise ValueError("Failed to parse agent response")
                
                # Execute action
                obs, reward, done, info = self.env.step(action)
                
                # Log step
                action_str = response_text.replace("\n", " ")[:100]  # Truncate for logging
                self.log_step(step, action_str, reward.total_reward, done, last_error)
                
                total_reward += reward.total_reward
                all_rewards.append(reward.total_reward)
                steps_taken = step
                last_error = None
                
                if done:
                    break
            
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                self.log_step(step, "<error>", 0.0, True, error_msg)
                break
        
        # Calculate success
        success = steps_taken > 0 and total_reward > 0.1
        
        # Log end
        self.log_end(success, steps_taken, total_reward, all_rewards)
        
        return success, steps_taken, total_reward, all_rewards


def main():
    """Main entry point - runs inference with configurable episode limit."""
    import time
    
    # Read max episodes from environment (default: 1 to preserve credits)
    max_episodes = int(os.getenv("MAX_EPISODES", "1"))
    
    episode_count = 0
    
    try:
        runner = InferenceRunner()
        
        while episode_count < max_episodes:
            episode_count += 1
            print(f"\n{'='*60}", flush=True)
            print(f"Episode {episode_count}/{max_episodes}", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            try:
                success, steps, score, rewards = runner.run_episode()
                
                if not success:
                    print(f"[WARNING] Episode {episode_count} failed, continuing...", flush=True)
            
            except Exception as e:
                print(f"[ERROR] Episode {episode_count} error: {e}", flush=True)
            
            # Wait before next episode (only if not last episode)
            if episode_count < max_episodes:
                print(f"[INFO] Waiting 5 seconds before next episode...\n", flush=True)
                time.sleep(5)
        
        print(f"\n[INFO] Completed {episode_count} episode(s). Exiting.", flush=True)
    
    except KeyboardInterrupt:
        print(f"\n[INFO] Interrupted by user after {episode_count} episodes.", flush=True)
        exit(0)
    except Exception as e:
        print(f"[ERROR] Fatal error: {e}", flush=True)
        exit(1)


if __name__ == "__main__":
    main()
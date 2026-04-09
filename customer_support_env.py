"""
AI Customer Support Resolution System - OpenEnv Environment

Real-world task: Help AI agents learn to resolve customer support tickets efficiently.
Tasks range from email triage (easy) to multi-turn complex resolution (hard).
"""

import json
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Three difficulty levels as required by OpenEnv spec."""
    EASY = "email_triage"  # Categorize incoming emails
    MEDIUM = "ticket_priority"  # Assign priorities and next steps
    HARD = "multi_turn_resolution"  # Multi-turn ticket resolution


class Priority(str, Enum):
    """Support ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Category(str, Enum):
    """Email categories for triage."""
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEEDBACK = "feedback"
    OTHER = "other"


class Observation(BaseModel):
    """Observation returned by the environment."""
    
    task_type: TaskType = Field(..., description="Current task type (easy/medium/hard)")
    ticket_id: str = Field(..., description="Unique ticket identifier")
    customer_message: str = Field(..., description="Customer's message or email content")
    previous_context: Optional[str] = Field(default=None, description="Prior conversation history")
    timestamp: str = Field(..., description="When the ticket was received")
    customer_sentiment: str = Field(..., description="Detected sentiment: positive/neutral/negative")
    current_resolution_steps: List[str] = Field(default_factory=list, description="Steps taken so far")
    step_number: int = Field(..., description="Current step in episode")


class Action(BaseModel):
    """Action that the agent can take."""
    
    task_type: TaskType = Field(..., description="Which task type this action applies to")
    action_type: str = Field(..., description="easy: 'categorize', medium: 'assign_priority', hard: 'respond'")
    
    # For email triage (easy)
    category: Optional[Category] = Field(default=None, description="[EASY] Category assignment")
    
    # For ticket priority (medium)
    priority: Optional[Priority] = Field(default=None, description="[MEDIUM] Priority level")
    suggested_next_step: Optional[str] = Field(default=None, description="[MEDIUM] What to do next")
    
    # For multi-turn resolution (hard)
    response_text: Optional[str] = Field(default=None, description="[HARD] Agent response to customer")


class Reward(BaseModel):
    """Reward signal with detailed breakdown."""
    
    total_reward: float = Field(..., description="Total reward for this step (0.0-1.0)")
    correctness_score: float = Field(..., description="How correct the action was (0.0-1.0)")
    efficiency_bonus: float = Field(..., description="Bonus for efficiency (0.0-0.2)")
    customer_satisfaction: float = Field(..., description="Estimated satisfaction signal (0.0-1.0)")
    details: str = Field(..., description="Human-readable explanation")


class CustomerSupportEnv:
    """
    AI Customer Support Resolution System Environment.
    
    Real-world task: Train AI agents to handle customer support tickets efficiently.
    Implements OpenEnv standard: step(), reset(), state()
    """
    
    # Synthetic data for various support scenarios
    SAMPLE_TICKETS = {
        "email_triage": [
            {
                "id": "T001",
                "message": "My billing statement shows incorrect charges from last month. Can you help?",
                "correct_category": Category.BILLING,
                "sentiment": "negative",
                "context": None
            },
            {
                "id": "T002",
                "message": "How do I enable two-factor authentication on my account?",
                "correct_category": Category.TECHNICAL,
                "sentiment": "neutral",
                "context": None
            },
            {
                "id": "T003",
                "message": "Great service! I love the new dashboard features.",
                "correct_category": Category.FEEDBACK,
                "sentiment": "positive",
                "context": None
            },
            {
                "id": "T004",
                "message": "I can't log in to my account. It says invalid credentials but I'm sure my password is correct.",
                "correct_category": Category.ACCOUNT,
                "sentiment": "negative",
                "context": None
            },
            {
                "id": "T005",
                "message": "What's the best way to export my data?",
                "correct_category": Category.TECHNICAL,
                "sentiment": "neutral",
                "context": None
            },
        ],
        "ticket_priority": [
            {
                "id": "TP001",
                "message": "Payment processing is down for all users across Europe.",
                "correct_priority": Priority.URGENT,
                "correct_step": "escalate_to_engineering",
                "context": "Critical production issue",
                "sentiment": "negative"
            },
            {
                "id": "TP002",
                "message": "Can you help me understand the pricing page?",
                "correct_priority": Priority.LOW,
                "correct_step": "send_documentation",
                "context": "General inquiry",
                "sentiment": "neutral"
            },
            {
                "id": "TP003",
                "message": "3 customers have reported missing data after the update.",
                "correct_priority": Priority.HIGH,
                "correct_step": "investigate_data_loss",
                "context": "Data integrity concern",
                "sentiment": "negative"
            },
            {
                "id": "TP004",
                "message": "My subscription renewal failed yesterday.",
                "correct_priority": Priority.HIGH,
                "correct_step": "process_payment_retry",
                "context": "Billing issue",
                "sentiment": "negative"
            },
        ],
        "multi_turn_resolution": [
            {
                "id": "MTR001",
                "initial_message": "My API key stopped working this morning",
                "followups": [
                    ("I regenerated it and it still doesn't work", "technical_investigation"),
                    ("I'm getting 401 errors consistently", "auth_verification"),
                    ("Yes, I've restarted the service multiple times", "full_resolution")
                ],
                "sentiment_progression": ["negative", "negative", "frustrated"],
                "resolution_path": ["restart_service", "verify_api_scope", "escalate_support"]
            },
            {
                "id": "MTR002",
                "initial_message": "I'm trying to migrate from competitor X but I'm stuck",
                "followups": [
                    ("The data mapping seems wrong", "data_validation"),
                    ("Can I get an extension on my plan to work through this?", "escalation")
                ],
                "sentiment_progression": ["neutral", "concerned", "hopeful"],
                "resolution_path": ["provide_migration_guide", "validate_data", "offer_extension"]
            },
        ]
    }
    
    # Grading rubrics for each task
    GRADING_RUBRICS = {
        Category.BILLING: 0.95,
        Category.TECHNICAL: 0.88,
        Category.ACCOUNT: 0.90,
        Category.FEEDBACK: 0.80,
        Category.OTHER: 0.70,
    }
    
    PRIORITY_RUBRICS = {
        Priority.URGENT: 0.95,
        Priority.HIGH: 0.85,
        Priority.MEDIUM: 0.70,
        Priority.LOW: 0.60,
    }
    
    def __init__(self, task_type: TaskType = TaskType.EASY, seed: int = 42):
        """Initialize environment."""
        random.seed(seed)
        self.task_type = task_type
        self.max_steps = 8
        self.current_step = 0
        self.episode_rewards = []
        self.current_ticket = None
        self.current_followup_idx = 0
        
    def reset(self) -> Observation:
        """Reset environment and return initial observation."""
        self.current_step = 0
        self.episode_rewards = []
        self.current_followup_idx = 0
        
        # Select random ticket for this task
        tickets = self.SAMPLE_TICKETS[self.task_type.value]
        self.current_ticket = random.choice(tickets)
        
        return Observation(
            task_type=self.task_type,
            ticket_id=self.current_ticket["id"],
            customer_message=self.current_ticket.get("message") or self.current_ticket.get("initial_message"),
            previous_context=self.current_ticket.get("context"),
            timestamp=datetime.now().isoformat(),
            customer_sentiment=self.current_ticket.get("sentiment", "neutral"),
            current_resolution_steps=[],
            step_number=self.current_step
        )
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        """Execute one step of the environment."""
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        # Validate action matches task type
        if action.task_type != self.task_type:
            reward_obj = Reward(
                total_reward=-0.1,
                correctness_score=0.0,
                efficiency_bonus=0.0,
                customer_satisfaction=-0.1,
                details=f"Task mismatch: expected {self.task_type.value}, got {action.task_type.value}"
            )
            self.episode_rewards.append(reward_obj.total_reward)
            return self._get_observation(), reward_obj, done, {"error": "task_mismatch"}
        
        # Grade the action based on task type
        if self.task_type == TaskType.EASY:
            reward_obj = self._grade_triage(action)
        elif self.task_type == TaskType.MEDIUM:
            reward_obj = self._grade_priority(action)
        else:  # HARD
            reward_obj = self._grade_resolution(action)
        
        self.episode_rewards.append(reward_obj.total_reward)
        
        # Multi-turn resolution: advance to next followup
        if self.task_type == TaskType.HARD and not done:
            self.current_followup_idx += 1
        
        info = {
            "step": self.current_step,
            "task_type": self.task_type.value,
            "reward_details": reward_obj.details
        }
        
        return self._get_observation(), reward_obj, done, info
    
    def state(self) -> Dict:
        """Return current environment state."""
        return {
            "task_type": self.task_type.value,
            "current_step": self.current_step,
            "current_ticket": self.current_ticket,
            "episode_rewards": self.episode_rewards,
            "total_reward": sum(self.episode_rewards) if self.episode_rewards else 0.0,
            "max_steps": self.max_steps
        }
    
    # ============= Grading methods for each task =============
    
    def _grade_triage(self, action: Action) -> Reward:
        """Grade email triage task (EASY)."""
        if action.action_type != "categorize" or not action.category:
            return Reward(
                total_reward=0.05,  # Minimum non-zero score
                correctness_score=0.05,
                efficiency_bonus=0.0,
                customer_satisfaction=0.0,
                details="Invalid action format for triage task"
            )
        
        correct_category = self.current_ticket.get("correct_category")
        is_correct = action.category == correct_category
        
        correctness_score = max(0.05, min(0.95, 0.95 if is_correct else 0.3))  # Strictly (0, 1)
        # Efficiency bonus: fewer steps is better
        efficiency_bonus = max(0.01, min(0.90, 0.15 * (1.0 - self.current_step / self.max_steps)))  # Strictly (0, 1)
        
        # Sentiment affects satisfaction
        sentiment_factor = {"positive": 1.0, "neutral": 0.8, "negative": 0.6}.get(
            self.current_ticket.get("sentiment", "neutral"), 0.8
        )
        customer_satisfaction = max(0.01, min(0.90, correctness_score * sentiment_factor))  # Strictly (0, 1)
        
        total_reward = max(0.01, min(0.99, correctness_score * 0.7 + efficiency_bonus + customer_satisfaction * 0.1))
        
        details = f"Categorized as '{action.category.value}' (correct: {correct_category.value}). " \
                  f"Match: {is_correct}. Efficiency bonus: {efficiency_bonus:.2f}"
        
        return Reward(
            total_reward=total_reward,
            correctness_score=correctness_score,
            efficiency_bonus=efficiency_bonus,
            customer_satisfaction=customer_satisfaction,
            details=details
        )
    
    def _grade_priority(self, action: Action) -> Reward:
        """Grade ticket priority assignment (MEDIUM)."""
        if action.action_type != "assign_priority" or not action.priority or not action.suggested_next_step:
            return Reward(
                total_reward=0.05,  # Minimum non-zero score
                correctness_score=0.05,
                efficiency_bonus=0.0,
                customer_satisfaction=0.0,
                details="Invalid action format for priority assignment"
            )
        
        correct_priority = self.current_ticket.get("correct_priority")
        correct_step = self.current_ticket.get("correct_step")
        
        priority_match = action.priority == correct_priority
        step_match = action.suggested_next_step.lower() == correct_step.lower()
        
        priority_correctness = 0.95 if priority_match else 0.5  # Partial credit for close priority
        step_correctness = 0.95 if step_match else 0.3  # Penalize wrong next step more
        
        correctness_score = max(0.05, min(0.95, (priority_correctness + step_correctness) / 2.0))  # Strictly (0, 1)
        efficiency_bonus = max(0.01, min(0.90, 0.12 * (1.0 - self.current_step / self.max_steps)))  # Strictly (0, 1)
        
        sentiment_factor = {"positive": 0.9, "neutral": 0.8, "negative": 0.7}.get(
            self.current_ticket.get("sentiment", "neutral"), 0.8
        )
        customer_satisfaction = max(0.01, min(0.90, correctness_score * sentiment_factor))  # Strictly (0, 1)
        
        total_reward = max(0.01, min(0.99, correctness_score * 0.6 + efficiency_bonus + customer_satisfaction * 0.25))
        
        details = f"Priority: {action.priority.value} (correct: {correct_priority.value}). " \
                  f"Next step: {action.suggested_next_step} (correct: {correct_step}). " \
                  f"Match: {priority_match and step_match}"
        
        return Reward(
            total_reward=total_reward,
            correctness_score=correctness_score,
            efficiency_bonus=efficiency_bonus,
            customer_satisfaction=customer_satisfaction,
            details=details
        )
    
    def _grade_resolution(self, action: Action) -> Reward:
        """Grade multi-turn resolution (HARD)."""
        if action.action_type != "respond" or not action.response_text:
            return Reward(
                total_reward=0.05,  # Minimum non-zero score
                correctness_score=0.05,
                efficiency_bonus=0.0,
                customer_satisfaction=0.0,
                details="Invalid action format for resolution"
            )
        
        # Check response quality
        response_length = len(action.response_text.split())
        is_substantive = response_length > 5  # Minimum substantive response
        
        # Check if response addresses followup
        current_followup = self._get_current_followup_text()
        addresses_issue = any(
            keyword in action.response_text.lower()
            for keyword in ["help", "try", "issue", "problem", "work", "check", "restart", "verify", "escalate"]
        )
        
        correctness_score = max(0.05, min(0.95, (0.90 if is_substantive else 0.3) * (0.95 if addresses_issue else 0.5)))  # Strictly (0, 1)
        efficiency_bonus = max(0.01, min(0.90, 0.08 * (1.0 - self.current_step / self.max_steps)))  # Strictly (0, 1)
        
        # Sentiment improves if response is empathetic
        is_empathetic = any(
            word in action.response_text.lower()
            for word in ["understand", "sorry", "appreciate", "help", "glad", "thank"]
        )
        sentiment_factor = {"positive": 0.95, "neutral": 0.75, "negative": 0.5}.get(
            self._get_current_sentiment(), "neutral"
        )
        customer_satisfaction = max(0.01, min(0.90, (0.6 if is_empathetic else 0.4) * sentiment_factor))  # Strictly (0, 1)
        
        total_reward = max(0.01, min(0.99, correctness_score * 0.5 + efficiency_bonus + customer_satisfaction * 0.35))
        
        details = f"Response length: {response_length} words. Substantive: {is_substantive}. " \
                  f"Addresses issue: {addresses_issue}. Empathetic: {is_empathetic}. " \
                  f"Quality score: {correctness_score:.2f}"
        
        return Reward(
            total_reward=total_reward,
            correctness_score=correctness_score,
            efficiency_bonus=efficiency_bonus,
            customer_satisfaction=customer_satisfaction,
            details=details
        )
    
    # ============= Helper methods =============
    
    def _get_observation(self) -> Observation:
        """Get current observation."""
        if self.task_type == TaskType.HARD:
            customer_message = self._get_current_followup_text()
            sentiment = self._get_current_sentiment()
        else:
            customer_message = self.current_ticket.get("message") or self.current_ticket.get("initial_message")
            sentiment = self.current_ticket.get("sentiment", "neutral")
        
        return Observation(
            task_type=self.task_type,
            ticket_id=self.current_ticket["id"],
            customer_message=customer_message,
            previous_context=self.current_ticket.get("context"),
            timestamp=datetime.now().isoformat(),
            customer_sentiment=sentiment,
            current_resolution_steps=[],
            step_number=self.current_step
        )
    
    def _get_current_followup_text(self) -> str:
        """Get current followup message for multi-turn."""
        if self.task_type != TaskType.HARD:
            return self.current_ticket.get("initial_message", "")
        
        if self.current_followup_idx == 0:
            return self.current_ticket.get("initial_message", "")
        
        if self.current_followup_idx <= len(self.current_ticket.get("followups", [])):
            return self.current_ticket["followups"][self.current_followup_idx - 1][0]
        
        return "Problem resolved."
    
    def _get_current_sentiment(self) -> str:
        """Get current sentiment for multi-turn."""
        if self.task_type != TaskType.HARD:
            return self.current_ticket.get("sentiment", "neutral")
        
        sentiment_progression = self.current_ticket.get("sentiment_progression", [])
        if self.current_followup_idx < len(sentiment_progression):
            return sentiment_progression[self.current_followup_idx]
        
        return "positive"  # Assume resolved


if __name__ == "__main__":
    # Quick test
    for task in TaskType:
        env = CustomerSupportEnv(task_type=task)
        obs = env.reset()
        print(f"\n{task.value}: {obs.ticket_id}")
        print(f"Message: {obs.customer_message[:100]}...")

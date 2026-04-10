---
title: Customer Support Resolution
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

# 🤖 AI Customer Support Resolution System

> A production-inspired [OpenEnv](https://github.com/openenv/spec) environment for training AI agents to handle customer support tickets — from simple email triage to complex multi-turn conversations.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-compatible-blue)](https://github.com/openenv/spec)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![HF Space](https://img.shields.io/badge/🤗%20Hugging%20Face-Space-orange)](https://huggingface.co/spaces/Saurav-Kewat/customer-support-resolution)

---

## Motivation

Customer support automation is a high-impact real-world problem. Organizations need AI that can:

- **Triage tickets** without misclassification
- **Prioritize urgent issues** to prevent churn
- **Resolve conversations** with empathy and substance

This environment provides structured feedback via correctness, efficiency, and satisfaction signals — enabling agents to learn these skills through dense rewards.

---

## Tasks

Three progressively harder tasks mirror actual support workflows:

| Task | Difficulty | Objective | Grading |
|------|-----------|-----------|---------|
| **Email Triage** | Easy | Categorize emails into 5 categories | Exact match (binary) |
| **Ticket Priority** | Medium | Assign priority + recommend next step | Partial credit for close matches |
| **Multi-turn Resolution** | Hard | Conduct empathetic, substantive conversations | Quality, empathy, and resolution progress |

### Email Triage (Easy)

Classify emails as: `billing`, `technical`, `account`, `feedback`, or `other`.

```json
{"action_type": "categorize", "category": "billing"}
```

### Ticket Priority (Medium)

Assign priority (`urgent`/`high`/`medium`/`low`) and a next step (`escalate_to_engineering`, `process_payment_retry`, `send_documentation`, `investigate_data_loss`, `offer_extension`).

```json
{"action_type": "assign_priority", "priority": "urgent", "suggested_next_step": "escalate_to_engineering"}
```

### Multi-turn Resolution (Hard)

Provide helpful, empathetic responses across 3-4 turns. Graded on substantiveness, issue addressing, and empathy.

```json
{"action_type": "respond", "response_text": "I understand how frustrating this must be..."}
```

---

## Observation & Reward Spaces

**Observation** — Pydantic model with:

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | `str` | Unique ticket identifier |
| `customer_message` | `str` | Customer's current message |
| `previous_context` | `str?` | Background / conversation history |
| `customer_sentiment` | `str` | `positive` / `neutral` / `negative` |
| `step_number` | `int` | Current step (1–8) |

**Reward** — Multi-dimensional feedback:

| Component | Range | Description |
|-----------|-------|-------------|
| `total_reward` | (0, 1) | Overall score |
| `correctness_score` | (0, 1) | Accuracy of the action |
| `efficiency_bonus` | (0, 1) | Bonus for fewer steps |
| `customer_satisfaction` | (0, 1) | Estimated satisfaction signal |

All scores are strictly between 0 and 1 (exclusive).

---

## Baseline Scores

Running with **Qwen/Qwen2.5-72B-Instruct** (seed=42):

| Task | Avg Score | Success Rate |
|------|-----------|-------------|
| Email Triage | ~0.78 | 85% |
| Ticket Priority | ~0.65 | 72% |
| Multi-turn Resolution | ~0.52 | 58% |

---

## Quick Start

### Local

```bash
git clone https://github.com/Saurav-Kewat/customer-support-resolution.git
cd customer-support-resolution
pip install -r requirements.txt

export HF_TOKEN="your-token"
export API_BASE_URL="https://router.huggingface.co/v1"
python inference.py
```

### Docker

```bash
docker build -t customer-support-env .
docker run --rm -e HF_TOKEN=$HF_TOKEN -p 7860:7860 customer-support-env
```

### API Endpoints (served by the container)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Reset environment, get initial observation |
| `POST` | `/step` | Execute action, get (observation, reward, done, info) |
| `POST` | `/state` | Get current environment state |
| `GET` | `/` | Health check |

---

## Project Structure

```
├── customer_support_env.py   # Core environment (Pydantic models, graders)
├── inference.py              # Baseline inference script (runs all 3 tasks)
├── server.py                 # HTTP API server (reset/step/state)
├── openenv.yaml              # OpenEnv specification
├── Dockerfile                # Container configuration
├── requirements.txt          # Python dependencies
└── README.md
```

---

## Environment API

```python
from customer_support_env import CustomerSupportEnv, TaskType, Action, Category

env = CustomerSupportEnv(TaskType.EASY, seed=42)
obs = env.reset()

action = Action(task_type=TaskType.EASY, action_type="categorize", category=Category.BILLING)
obs, reward, done, info = env.step(action)

print(f"Reward: {reward.total_reward:.2f}")  # 0.75
print(f"Details: {reward.details}")
```

---

## OpenEnv Compliance

| Requirement | Status |
|-------------|--------|
| Pydantic Observation / Action / Reward | ✅ |
| `step()` → (obs, reward, done, info) | ✅ |
| `reset()` → observation | ✅ |
| `state()` → dict | ✅ |
| `openenv.yaml` with metadata | ✅ |
| 3 tasks (easy → hard) with graders | ✅ |
| Scores strictly in (0, 1) | ✅ |
| Dense rewards (not just at episode end) | ✅ |
| Baseline inference script with `HF_TOKEN` | ✅ |
| Dockerized deployment | ✅ |

---

## License

[MIT](LICENSE)

# Round 1 — Problem Statement

## 🎯 The Task

Build a complete, real-world OpenEnv environment that an AI agent can learn from through the standard:

* `step()`
* `reset()`
* `state()`
  API

---

## ✅ Key Requirements at a Glance

* Must simulate a **real-world task** (not games or toys)
* Implement full OpenEnv spec:

  * typed models
  * `step/reset/state`
  * `openenv.yaml`
* Minimum **3 tasks with agent graders** (easy → medium → hard, scores 0.0–1.0)
* Meaningful **reward function** with partial progress signals
* Baseline inference script with reproducible scores
* Deploy to **Hugging Face Spaces** + working Dockerfile
* README with:

  * environment description
  * action/observation spaces
  * setup instructions

---

# 📋 Detailed Requirements

## Functional Requirements

### 1. Real-world task simulation

* Environment must simulate a **business or human-use case**
* Not games, not toys
* Examples:

  * email triage
  * code review
  * data cleaning
  * scheduling
  * customer support
  * content moderation

---

### 2. OpenEnv spec compliance

Implement:

* Typed `Observation`, `Action`, `Reward` Pydantic models
* `step(action)` → returns observation, reward, done, info
* `reset()` → returns initial observation
* `state()` → returns current state
* `openenv.yaml` with metadata
* Must validate via OpenEnv

---

### 3. Minimum 3 tasks with graders

* Each task has:

  * a clear objective
  * programmatic grader (score 0.0–1.0)
* Tasks must scale difficulty:

  * easy → medium → hard
* Graders must validate:

  * correctness
  * success/failure criteria

---

### 4. Meaningful reward function

* Avoid binary rewards only
* Provide **dense feedback signals**
* Reward:

  * partial progress
  * task completion
* Penalize:

  * invalid actions
  * destructive behavior

---

### 5. Baseline inference script

* Uses OpenAI client to run model
* Reads API key from environment (`OPENAI_API_KEY`)
* Produces reproducible baseline scores

---

## Non-Functional Requirements

### 🚀 Deploy to Hugging Face Spaces

* Must run as containerized HF Space
* Tagged with OpenEnv

### 🐳 Containerized execution

* Provide working `Dockerfile`
* Must run via:

  * `docker build`
  * `docker run`

---

### 📚 Documentation

README must include:

* Environment description
* Motivation
* Action & observation space
* Task descriptions + difficulty
* Setup instructions
* Baseline scores

---

# 📊 Evaluation Criteria

| Parameter                      | Weight | Description                                     |
| ------------------------------ | ------ | ----------------------------------------------- |
| Real-world utility             | 30%    | Is it practical and useful?                     |
| Task & grader quality          | 25%    | Difficulty, correctness, measurable scoring     |
| Environment design             | 20%    | Clean structure, reward shaping, reset behavior |
| Code quality & spec compliance | 15%    | OpenEnv adherence, Docker, reproducibility      |
| Creativity & novelty           | 10%    | Unique idea, interesting mechanics              |

---

## 🧮 Scoring Breakdown

### Real-world utility (30%)

* 0–5: Toy/artificial
* 6–15: Valid domain, shallow modeling
* 16–25: Strong modeling, useful
* 26–30: Excellent, production-relevant

---

### Task & grader quality (25%)

* 3+ tasks with difficulty range
* Deterministic scoring
* Scores between 0.0–1.0
* Challenges real agents

---

### Environment design (20%)

* `reset()` returns clean state
* Actions/observations well defined
* Reward provides meaningful signal
* Episodes are logical

---

### Code quality (15%)

* OpenEnv validation passes
* Docker builds & runs
* HF Space deploys
* Baseline script reproducible

---

### Creativity (10%)

* Novel problem
* Interesting mechanics
* Reward shaping adds depth

---

# ⚙️ How Judging Works

### Phase 1: Automated Validation

* HF Space deploys
* OpenEnv compliance check
* Docker builds
* Baseline runs
* 3 tasks with graders

---

### Phase 2: Agent Evaluation

* Standard LLM agent (e.g., Nemotron 3 Super)
* Runs across environments
* Score variance measured

---

### Phase 3: Human Review

* Evaluated by Meta + Hugging Face engineers
* Focus:

  * real-world utility
  * creativity
  * robustness

---

# ❌ Disqualification Criteria

* Environment doesn’t deploy/run
* Plagiarized or trivial design
* Graders always return same score
* No baseline inference script

---

# ✅ Pre-Submission Checklist

* HF Space deploys (responds to reset)
* OpenEnv spec passes
* Docker builds successfully
* Baseline script runs end-to-end
* 3 tasks with graders implemented

---

## 🔑 Required Environment Variables

* `API_BASE_URL` (for LLM API)
* `MODEL_NAME`
* `HF_TOKEN`

---

## ⏱ Constraints

* Runtime per inference script: **< 20 minutes**
* Must run on CPU (no GPU required)

---



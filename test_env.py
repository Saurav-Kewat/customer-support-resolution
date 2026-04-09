"""Quick test of the customer support environment"""
from customer_support_env import CustomerSupportEnv, TaskType, Action, Category, Priority

# Test EASY task
print("Testing EASY task...")
env = CustomerSupportEnv(TaskType.EASY, seed=42)
obs = env.reset()
print(f'✓ Reset EASY task: ticket_id={obs.ticket_id}')

action = Action(task_type=TaskType.EASY, action_type='categorize', category=Category.BILLING)
obs, reward, done, info = env.step(action)
print(f'✓ Step completed: reward={reward.total_reward:.2f}, details={reward.details}')

state = env.state()
total = state['total_reward']
print(f'✓ State retrieved: total_reward={total:.2f}')

# Test MEDIUM task
print("\nTesting MEDIUM task...")
env2 = CustomerSupportEnv(TaskType.MEDIUM, seed=42)
obs2 = env2.reset()
print(f'✓ Reset MEDIUM task: ticket_id={obs2.ticket_id}')

action2 = Action(
    task_type=TaskType.MEDIUM,
    action_type='assign_priority',
    priority=Priority.URGENT,
    suggested_next_step='escalate_to_engineering'
)
obs2, reward2, done2, info2 = env2.step(action2)
print(f'✓ Step completed: reward={reward2.total_reward:.2f}')

# Test HARD task
print("\nTesting HARD task...")
env3 = CustomerSupportEnv(TaskType.HARD, seed=42)
obs3 = env3.reset()
print(f'✓ Reset HARD task: ticket_id={obs3.ticket_id}')

action3 = Action(
    task_type=TaskType.HARD,
    action_type='respond',
    response_text='I understand your issue. Let me help you troubleshoot this problem step by step.'
)
obs3, reward3, done3, info3 = env3.step(action3)
print(f'✓ Step completed: reward={reward3.total_reward:.2f}')

print('\n✓✓✓ All environment tests passed! ✓✓✓')

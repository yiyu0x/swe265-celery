from tasks import add, process_data, long_task
import time
import random

def test_tasks():
    """Send multiple Celery tasks for testing"""
    print("Starting Celery tasks...\n")
    
    # Test the add task
    print("=== Testing add tasks ===")
    results_add = []
    for i in range(5):
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        print(f"Sending task {i+1}: add({a}, {b})")
        result = add.delay(a, b)
        results_add.append((result, a, b))
        time.sleep(0.3)

    # Test the process_data task
    print("\n=== Testing process_data tasks ===")
    results_process = []
    for i in range(3):
        data_size = random.randint(5, 20)
        print(f"Sending task {i+1}: process_data({data_size})")
        result = process_data.delay(data_size)
        results_process.append((result, data_size))
        time.sleep(0.3)
    
    # Test the long_task
    print("\n=== Testing long_task ===")
    duration = random.randint(2, 8)
    print(f"Sending long_task({duration})")
    result_long = long_task.delay(duration)
    
    # Wait and check add results
    print("\n=== Results for add tasks ===")
    for i, (result, a, b) in enumerate(results_add):
        try:
            value = result.get(timeout=5)
            print(f"Task {i+1}: {a} + {b} = {value}")
        except Exception as e:
            print(f"Task {i+1} failed: {e}")
    
    # Wait and check process_data results
    print("\n=== Results for process_data tasks ===")
    for i, (result, data_size) in enumerate(results_process):
        try:
            value = result.get(timeout=10)
            print(f"Task {i+1} (data_size={data_size}): {value}")
        except Exception as e:
            print(f"Task {i+1} failed: {e}")
    
    # Wait and check long_task results
    print("\n=== Results for long_task ===")
    try:
        value = result_long.get(timeout=duration + 2)
        print(f"Long task (duration={duration}): {value}")
    except Exception as e:
        print(f"Long task failed: {e}")
    
    print("\nAll tasks completed!")

def run_mixed_workload():
    """Run a mixed workload of tasks with different priorities"""
    print("Starting mixed workload test...\n")
    
    # Queue multiple tasks
    task_count = {'add': 0, 'process': 0, 'long': 0}
    
    for _ in range(10):
        task_type = random.choice(['add', 'process', 'long'])
        
        if task_type == 'add':
            a, b = random.randint(1, 100), random.randint(1, 100)
            add.delay(a, b)
            task_count['add'] += 1
            
        elif task_type == 'process':
            data_size = random.randint(5, 30)
            process_data.delay(data_size)
            task_count['process'] += 1
            
        else:
            duration = random.randint(1, 3)
            long_task.delay(duration)
            task_count['long'] += 1

    print("Queued mixed workload:")
    print(f"- {task_count['add']} add tasks")
    print(f"- {task_count['process']} process_data tasks")
    print(f"- {task_count['long']} long_task tasks")
    print("\nCheck Flower or Prometheus for task metrics!")

if __name__ == "__main__":
    choice = input("Select test mode:\n1. Test individual tasks\n2. Run mixed workload\nChoice (1/2): ")
    
    if choice == "2":
        run_mixed_workload()
    else:
        test_tasks()
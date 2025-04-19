import os
import time
import random
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

app = Celery("demo", broker=broker_url, backend=result_backend)

@app.task
def add(x, y):
    return x + y

@app.task(bind=True, max_retries=3)
def process_data(self, data_size):
    """Process data with possible retry logic
    
    Simulates a data processing task that may occasionally fail
    and uses Celery's retry mechanism.
    """
    # Simulate processing time based on data size
    process_time = data_size * 0.1
    time.sleep(process_time)
    
    # Randomly fail (10% chance) to demonstrate retry
    if random.random() < 0.1:
        self.retry(countdown=2)
        
    return f"Processed {data_size} units of data in {process_time:.2f} seconds"

@app.task
def long_task(duration=5):
    """A long running task that simulates heavy processing
    
    Good for demonstrating task monitoring and timeouts
    """
    time.sleep(duration)
    return f"Completed long task that ran for {duration} seconds"
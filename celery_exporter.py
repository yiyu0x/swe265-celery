import time
import sys
from prometheus_client import start_http_server, Counter, Gauge, Summary
from celery import Celery
from celery.events import EventReceiver
from kombu import Connection
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Metric definitions
TASKS_EXECUTED = Counter('celery_tasks_executed', 'Number of executed tasks', ['task_name', 'state'])
TASKS_RUNTIME = Summary('celery_task_runtime', 'Task runtime (seconds)', ['task_name'])
WORKERS_ONLINE = Gauge('celery_workers_online', 'Number of online workers', ['hostname'])

# Add a simple test metric to confirm exporter is working
EXPORTER_UP = Gauge('celery_exporter_up', 'Indicates if the celery exporter is up')
EXPORTER_UP.set(1)  # Set to 1, indicating the exporter is running

# New metrics for total tasks
TOTAL_TASKS_EXECUTED = Counter('celery_total_tasks_executed', 'Total number of executed tasks')
TOTAL_TASKS_RECEIVED = Counter('celery_total_tasks_received', 'Total number of received tasks')
REGISTERED_TASKS = Gauge('celery_registered_tasks', 'Number of registered task types')
REGISTERED_TASK_NAMES = Gauge('celery_task_registered', 'Registered task in Celery', ['task_name'])

def monitor_events():
    """Monitor Celery events"""
    broker_url = 'amqp://user:pass@rabbitmq:5672//'
    app = Celery(broker=broker_url)
    
    logger.info(f"Celery exporter starting with broker: {broker_url}")
    
    while True:
        try:
            with Connection(broker_url) as conn:
                logger.info("Connected to message broker, starting to capture events...")
                
                def on_event(event):
                    """Generic handler for all events"""
                    event_type = event.get('type')
                    
                    # Filter out worker-heartbeat events from logs
                    if event_type != 'worker-heartbeat':
                        logger.info(f"Received event: {event_type}")
                    
                    if event_type == 'task-received':
                        task_name = event.get('name', 'unknown')
                        TASKS_EXECUTED.labels(task_name=task_name, state='received').inc()
                        TOTAL_TASKS_RECEIVED.inc()
                    
                    elif event_type == 'task-succeeded':
                        task_name = event.get('name', 'unknown')
                        TASKS_EXECUTED.labels(task_name=task_name, state='succeeded').inc()
                        TOTAL_TASKS_EXECUTED.inc()
                        runtime = event.get('runtime', 0)
                        TASKS_RUNTIME.labels(task_name=task_name).observe(runtime)
                    
                    elif event_type == 'task-failed':
                        task_name = event.get('name', 'unknown')
                        TASKS_EXECUTED.labels(task_name=task_name, state='failed').inc()
                        TOTAL_TASKS_EXECUTED.inc()  # Count failed tasks in total execution
                    
                    elif event_type == 'worker-online':
                        WORKERS_ONLINE.labels(hostname=event.get('hostname', 'unknown')).inc()
                    
                    elif event_type == 'worker-heartbeat':
                        WORKERS_ONLINE.labels(hostname=event.get('hostname', 'unknown')).set(1)
                    
                    elif event_type == 'worker-offline':
                        WORKERS_ONLINE.labels(hostname=event.get('hostname', 'unknown')).dec()
                
                # Enable Celery events
                with app.connection() as connection:
                    recv = EventReceiver(
                        connection,
                        handlers={'*': on_event},  # Capture all events
                    )
                    logger.info("Starting Celery event monitoring...")
                    recv.capture(limit=None, timeout=None)
        
        except KeyboardInterrupt:
            logger.info("Celery exporter stopping...")
            break
        except Exception as e:
            logger.error(f"Error in event monitoring: {e}")
            logger.info("Reconnecting in 5 seconds...")
            time.sleep(5)  # Wait before reconnecting after error

def update_registered_tasks():
    """Periodically fetch and update the list of registered tasks"""
    broker_url = 'amqp://user:pass@rabbitmq:5672//'
    app = Celery(broker=broker_url)
    
    while True:
        try:
            # Connect to a worker to get registered tasks
            i = app.control.inspect()
            registered = i.registered()
            
            if registered:
                # Reset metrics before updating
                REGISTERED_TASKS.set(0)
                
                all_tasks = set()
                for worker, tasks in registered.items():
                    for task in tasks:
                        all_tasks.add(task)
                
                # Set the count of registered tasks
                REGISTERED_TASKS.set(len(all_tasks))
                
                # Create individual metrics for each registered task
                for task in all_tasks:
                    REGISTERED_TASK_NAMES.labels(task_name=task).set(1)
                    
                logger.info(f"Updated registered tasks: {len(all_tasks)} tasks found")
            else:
                logger.warning("Failed to retrieve registered tasks, no active workers")
                
        except Exception as e:
            logger.error(f"Error updating registered tasks: {e}")
            
        # Update every 60 seconds
        time.sleep(60)

def start_exporters():
    """Start all required exporter threads"""
    # Start HTTP server for Prometheus metrics
    try:
        start_http_server(8888)
        logger.info("Prometheus metrics server started on port 8888")
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        return False
    
    # Start event listener in a separate thread
    threading.Thread(target=monitor_events, daemon=True).start()
    
    # Start registered tasks updater in a separate thread
    threading.Thread(target=update_registered_tasks, daemon=True).start()
    
    # Keep main thread alive without logging
    try:
        while True:
            time.sleep(60)  # Sleep quietly without logging
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    logger.info("Celery exporter initializing...")
    start_exporters()
from celery import Celery
import os

INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'Worker-1')

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@app.task
def send_email(to, subject, body):
    print(f"[{INSTANCE_NAME}] Sending email to {to}: {subject}")
    # Email logic here
    return f"Email sent to {to}"

@app.task
def process_order(order_id):
    print(f"[{INSTANCE_NAME}] Processing order {order_id}")
    # Order processing logic
    return f"Order {order_id} processed"

if __name__ == '__main__':
    app.worker_main(['worker', '--loglevel=info', '-Q', 'default', '-n', f'{INSTANCE_NAME}@%h'])
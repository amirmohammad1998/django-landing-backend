Landing Page Backend

🚀 Overview

This document details the architecture, setup, and operational procedures for the backend system supporting a high-traffic landing page. This system is engineered for massive scalability, reliability, and asynchronous processing, leveraging modern containerization and distributed computing patterns.

The core functionality revolves around the non-blocking registration of user mobile numbers from the landing page. To maintain responsiveness under heavy load, the primary persistence of registration requests is handled asynchronously using Celery. Validated numbers are stored in PostgreSQL, while comprehensive request metadata and logs are stored in MongoDB, adhering strictly to the Single Responsibility Principle (SRP).

The entire environment is orchestrated using Docker Compose, ensuring environmental parity between development, staging, and production. Communication between asynchronous workers and the main application is managed via RabbitMQ (as the message broker) and Redis (as the result backend and cache).



🧠 Tech Stack Deep Dive

The selection of technologies was driven by the need for high throughput, fault tolerance, and clear separation of concerns.

Core Web Framework





Django + DRF (Django Rest Framework): Provides a robust, mature ORM, built-in security features, and rapid API development capabilities. DRF handles serialization, authentication (though minimal for this endpoint), and request/response validation.

Databases





PostgreSQL:





Purpose: Source of truth for validated and accepted user registrations. Its ACID compliance ensures data integrity for the primary business data (the user phone numbers).



Schema Management: Handled via Django Migrations.



MongoDB:





Purpose: Used exclusively for high-volume, write-heavy logging of every incoming request, regardless of validation success or failure. This decoupling prevents logging bottlenecks from impacting API latency (SRP implementation).



Tooling: Mongo Express is used for a quick web interface to inspect the log data.

Asynchronous Processing & Messaging





Celery: The primary tool for offloading heavy, time-consuming, or non-essential tasks from the main request/response cycle. In this setup, validation persistence and logging are pushed to Celery workers.



RabbitMQ: Functions as the Message Broker for Celery. It reliably queues tasks sent by the Django application, ensuring that tasks are not lost if a worker crashes temporarily.





Configuration: Tasks are sent to the default RabbitMQ instance running within the Docker network.



Redis: Serves two critical roles:





Celery Result Backend: Stores the status and final result of executed Celery tasks, allowing the system to check task progress if necessary.



Caching Layer: Used by Django/DRF components for quick lookups (e.g., session data, rate limiting counters).

Operations & Monitoring





Docker Compose: Simplifies the entire multi-service deployment into a single, reproducible file (docker-compose.yml), managing the networking between Django, PostgreSQL, MongoDB, RabbitMQ, and Redis.



Gunicorn + Nginx:





Gunicorn: The production WSGI server running the Django application, handling multiple worker processes for concurrency.



Nginx: Acts as a reverse proxy, handling SSL termination (in a production setting), static file serving, and crucially, load balancing/request termination before passing traffic to Gunicorn.



Flower: A web-based tool for monitoring and managing Celery clusters. Essential for debugging task queues, inspecting worker status, and managing task retries.



⚙️ Installation & Run Procedures

These instructions detail the process for setting up the complete, containerized environment.

1️⃣ Clone Repository

Obtain the source code from the designated repository.

git clone https://github.com/django-landing-backend.git
cd landing_page_backend


2️⃣ Environment Variables Configuration

A secure and isolated configuration is achieved using environment variables managed via a .env file. This file must be created in the root directory of the project before starting the containers.

Create .env:

# PostgreSQL Configuration
POSTGRES_DB=landingdb
POSTGRES_USER=landinguser
POSTGRES_PASSWORD=landingpass
# Note: HOST is implicitly handled by Docker Compose service names.

# MongoDB Configuration
MONGO_INITDB_DATABASE=logs
# Default MongoDB user/pass setup is often omitted if not using authentication in local dev/test.

# Celery Broker (RabbitMQ) Configuration
# The hostname 'rabbitmq' refers to the service name in docker-compose.yml
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//

# Celery Result Backend (Redis) Configuration
CELERY_RESULT_BACKEND=redis://redis:6379/0

# RabbitMQ Credentials (for internal container communication)
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest

# Redis Hostname
REDIS_HOST=redis


3️⃣ Build & Run Containers

This command builds all necessary Docker images (including custom Dockerfiles for the Django application) and starts all defined services (Web, Postgres, Mongo, RabbitMQ, Redis, Flower) in detached mode (-d).

docker compose up -d --build






Verification: You can check the status of all running services using:

docker compose ps


4️⃣ Apply Database Migrations

Once the PostgreSQL container is running and accessible, Django needs to initialize its schema for the registration table.

# Execute the migration command inside the running 'web' container
docker compose exec web python manage.py migrate


5️⃣ Test API Endpoint (Registration)

After the services are fully initialized, the registration endpoint can be tested using curl. The system is designed to return HTTP 202 Accepted immediately, indicating the task has been queued, not that the final save is complete.

curl -X POST http://127.0.0.1/api/register/ \
     -H "Content-Type: application/json" \
     -d '{"phone": "09123456789"}'


✅ Expected Successful Response (Immediate):

{"message": "Your phone number has been accepted."}


Expected Status Code: HTTP_202_ACCEPTED





Post-check: Monitor Celery (via Flower) to confirm the task successfully processed the data into PostgreSQL and MongoDB.



🧩 API Structure Reference

The landing page communicates with the backend exclusively through a single high-volume endpoint.



Description: Asynchronously processes and registers the user's mobile number. The API returns immediately upon successful task queuing.

Request Body Parameters (JSON):

FieldTypeValidation & DescriptionphonestringRequired. Must adhere to the Iranian mobile number pattern: ^0\d{10}$ (11 digits starting with 0).referrerstringOptional. The source URL or campaign identifier that directed the user to the landing page.request_idstringOptional (though highly recommended by the frontend). A UUID generated by the client for idempotent tracking, passed through to the logs.



🧠 Observability and Monitoring

Maintaining visibility into a distributed system is paramount for high-traffic applications.

Flower (Celery Monitoring)





Access URL: http://localhost:5555



Usage: Use this interface to:





View the health and status of all Celery workers.



Inspect the task queue backlog (celery_broker_url).



Check the results of recently completed tasks (via the Redis backend).



Manually retry failed tasks or terminate stuck tasks.

Mongo Express (MongoDB UI)





Access URL: http://localhost:8081



Usage: Provides a web interface to directly query and inspect the logs database, allowing immediate verification that log entries (containing phone numbers, IP, timestamps, etc.) are being written correctly by the asynchronous tasks.

Application and Server Logs





Gunicorn/Application Logs: Standard output streams (stdout/stderr) from the web container contain Gunicorn access and error logs. These are accessible via Docker:

docker compose logs web




Error Tracing: The application entrypoint script (entrypoint.sh) is configured to ensure that Gunicorn logs detailed stack traces on HTTP errors, which are then captured by the container's logging driver.



🧰 Developer Notes and Architectural Principles

The following points detail critical design decisions and implementation requirements for maintaining the system's integrity under load.

Adherence to the Single Responsibility Principle (SRP)

The system strictly separates data handling responsibilities to maximize performance and resilience:





API Endpoint (views.py): Responsible only for immediate request validation (input format) and queueing the task (task.delay(...)). It must return 202 quickly.



PostgreSQL Persistence (tasks.py - Celery): Dedicated Celery task responsible only for complex validation (e.g., uniqueness checks, final data sanitization) and writing the final accepted record to the relational database.



MongoDB Logging (logs/utils.py - Celery): A separate, high-throughput Celery task responsible only for formatting the raw request data (including IP, headers, etc.) and persisting it to MongoDB.

Rate Limiting Implementation

To protect against simple denial-of-service or overwhelming the message broker, rate limiting is implemented directly within the RegisterPhoneView:





Mechanism: Utilizing Django Rest Framework's throttling mechanisms, likely based on IP address and/or request ID.



Storage Backend: Throttling counters should leverage the shared Redis instance for rapid, atomic increments and checks.



Throttling Strategy: Typically set to allow $N$ requests per minute per IP address.

IP Address Extraction Behind Proxies

Since the application is deployed behind Nginx (and potentially other load balancers in production), the client's true IP address cannot be reliably sourced from REMOTE_ADDR.





Required Header: The system must check the HTTP_X_FORWARDED_FOR header.



Logic: If this header exists, the leftmost IP address in the comma-separated list is considered the client's original IP. If it does not exist, fall back to request.META['REMOTE_ADDR']. This logic must be centralized, preferably in a custom middleware or within the request processing logic of the view function.

Data Integrity Assurance

The primary goal is to ensure that a request is either logged or successfully queued for PostgreSQL insertion, even if one service fails temporarily.





Transactional Safety: The Celery task handling the final registration should attempt to write to MongoDB and PostgreSQL. If the connection to one database fails during a critical step, a robust retry mechanism (via Celery configuration) must be in place.



Idempotency: While the primary goal is high throughput, the use of request_id allows for later auditing or potentially idempotent processing if needed, though the default behavior is "fire and forget" logging.



🗃️ Detailed Configuration Component Overviews (Conceptual)

(This section conceptually expands on required files that would exist within the repository structure)

(Django Application)

This Dockerfile ensures a lean production image:





Base Image: Uses a slim Python image (e.g., python:3.11-slim).



Dependencies: Installs system dependencies (e.g., gcc for compiling Python packages like psycopg2-binary).



Pip Install: Installs requirements (gunicorn, django, celery, djangorestframework, pymongo, etc.).



Code Copy: Copies the application source code.



Entrypoint: Sets the execution command via entrypoint.sh.



This script runs upon container startup, ensuring necessary pre-launch checks and setting production parameters for Gunicorn:

#!/bin/sh

# Wait for databases (Postgres and RabbitMQ) to be ready (basic health check loop)
# ... connection checks ...

# Run migrations if necessary (often done manually, but can be automated here)
# python manage.py migrate --noinput

# Start Gunicorn with optimized settings for production load
# Use N_WORKERS = (2 * CPU_CORES) + 1 strategy
echo "Starting Gunicorn..."
exec gunicorn landing_page_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gevent \
    --log-level info \
    --timeout 60


(Celery Tasks)

from celery import shared_task
from django.conf import settings
from .models import Registration
from logs.utils import log_request_data
from django.db import transaction

@shared_task(bind=True, max_retries=5)
def process_registration_task(self, phone_data: dict):
    """Handles the final persistence steps after initial API validation."""
    
    phone = phone_data.get('phone')
    referrer = phone_data.get('referrer')
    request_id = phone_data.get('request_id')
    ip_address = phone_data.get('ip_address')
    
    try:
        # 1. Write raw log data to MongoDB immediately (SRP adherence)
        log_request_data(
            collection_name='landing_attempts',
            data={
                'phone': phone,
                'referrer': referrer,
                'ip': ip_address,
                'request_id': request_id,
                'status': 'QUEUED'
            }
        )
        
        # 2. Database Transaction for PostgreSQL (Source of Truth)
        with transaction.atomic():
            # Check for duplicates before final save (complex validation)
            if Registration.objects.filter(phone=phone).exists():
                # Log this specific outcome in Mongo as well
                log_request_data(collection_name='landing_attempts', data={'phone': phone, 'status': 'DUPLICATE_DETECTED'})
                return {"status": "duplicate"}

            Registration.objects.create(
                phone=phone,
                referrer=referrer,
                request_id=request_id,
                ip_address=ip_address
            )
            
        # 3. Update Mongo Log Status to SUCCESS
        log_request_data(collection_name='landing_attempts', data={'request_id': request_id, 'status': 'SUCCESS_POSTGRES'})
        
        return {"status": "complete"}

    except Exception as exc:
        # If Postgres fails, allow Celery retry mechanism to handle it
        log_request_data(collection_name='landing_attempts', data={'request_id': request_id, 'status': f'FAILED_RETRY: {str(exc)}'})
        raise self.retry(exc=exc, countdown=2**self.request.retries)






📐 Advanced Scaling Considerations

The current setup provides excellent horizontal scaling potential due to the decoupled nature of the services.

Scaling Celery Workers

The number of active Celery workers is the primary lever for scaling processing capacity.

Calculation for Task Throughput:
If a single Celery task takes $T_{task}$ seconds to process (including MongoDB write and PostgreSQL commit), and we have $W$ workers, the sustained throughput $R$ is: [ R \approx \frac{W}{T_{task}} \text{ tasks per second} ]

If $T_{task}$ is observed to be 150ms (0.15s), and we run 10 workers:
[ R \approx \frac{10}{0.15} \approx 66.7 \text{ registrations per second} ]

In production environments, Celery workers should be auto-scaled based on the queue length reported by RabbitMQ, ensuring resources match the incoming traffic spikes observed at the landing page.

Database Connection Pooling

Given that the API servers (Gunicorn workers) and the background processing farm (Celery workers) both connect to PostgreSQL, connection management is crucial.





Gunicorn: Using an asynchronous worker class like gevent or eventlet (as hinted above) is often beneficial when dealing with I/O waits, even in a synchronous framework like Django, as it allows a single OS thread to manage many concurrent connections efficiently via cooperative multitasking.



Pooling Strategy: Implementing django-db-geventpool or similar pooling solutions might be necessary if connection setup/teardown overhead becomes significant, although modern PostgreSQL drivers handle pooling reasonably well when connections are managed carefully within the lifecycle of the worker process.

MongoDB Indexing Strategy

For the logging collection (landing_attempts), performance hinges on proper indexing, especially since we expect frequent writes and occasional reads for monitoring or debugging.

Required Indexes:





Primary Search Index: For debugging a specific request flow: [ \text{Index on } { \text{'request_id': 1}} ]



Time Series/Monitoring Index: For timeline analysis: [ \text{Index on } { \text{'_id': -1}} \text{ (Default MongoDB index on insertion time)} ]



Query Index: If reporting requires fetching all logs for a specific phone number (even if not successfully registered): [ \text{Index on } { \text{'phone': 1}} ]

Improper indexing on high-write collections like this can lead to severe I/O bottlenecks on the MongoDB cluster.



🔒 Security Considerations in the Backend

While this is a high-throughput endpoint, basic security hygiene must be enforced.

Input Sanitization and Validation





DRF Serializers: Enforce strict type and pattern matching on the phone field using regular expressions within the serializer, rejecting any input that doesn't match the ^0\d{10}$ pattern before the task is even queued.



XSS/Injection Prevention: Although the API is JSON-only, all data retrieved from user input (phone, referrer) and eventually written to the databases (Postgres/Mongo) must be treated as untrusted input. Since Django ORM handles SQL escaping, the primary concern shifts to ensuring that the referrer field does not contain harmful JavaScript if it were ever displayed in an administrative interface.

Broker Security (RabbitMQ)

By default, the setup uses the guest/guest user. In a production deployment:





Dedicated User: A dedicated user with specific rights (only capable of reading/writing to the necessary queues) must be created.



Strong Credentials: The RABBITMQ_DEFAULT_PASS must be replaced with a strong, non-default password stored securely in environment variables or a secrets manager.

Nginx Hardening

Nginx serves as the first line of defense:





Rate Limiting: Nginx can be configured for preliminary rate limiting based on IP before requests even hit the Gunicorn layer, effectively protecting against volumetric attacks that might bypass application-level rate limiting entirely.



Header Stripping: Ensure that headers like Server, X-Powered-By, etc., are stripped or modified to avoid leaking internal technology stack information.



Summary of Operational Workflow

The entire system operates based on this continuous, decoupled flow:





Client Request: User submits form data to POST /api/register/.



API Gateway (Nginx/Gunicorn): Receives request, strips headers, applies initial rate limits.



DRF View: Serializes and validates format. If valid, extracts IP (X-Forwarded-For), packages data, and calls process_registration_task.delay(...).



Immediate Response: Returns HTTP 202 Accepted to the client.



Message Broker (RabbitMQ): Receives the task message from Gunicorn/Django.



Celery Worker: Picks up the task from RabbitMQ.



Logging (MongoDB): The worker immediately writes the raw request data to MongoDB for immediate forensic analysis.



Persistence (PostgreSQL): The worker performs final business logic validation and commits the verified, canonical record to PostgreSQL within an atomic transaction.



Result Update (Redis): The Celery worker marks the task status as finished in Redis.



Monitoring (Flower): Observability tools track the health and completion rate across steps 6 through 9.

This detailed structure ensures maximum isolation between the fast synchronous path and the slower, complex asynchronous persistence tasks.

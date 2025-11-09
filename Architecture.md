Architecture Document - Landing Async System

System Architecture Document – Landing Page Backend



🎯 Objective

Design and implement a scalable, resilient backend for a high-traffic landing page leveraging Django, Celery, RabbitMQ, PostgreSQL, and MongoDB to ensure non-blocking request handling and reliable data persistence. The primary goal is to absorb potentially massive bursts of incoming traffic (e.g., from marketing campaigns) without degrading the user experience or losing critical registration data. The system must prioritize immediate user feedback (low latency response) over immediate backend processing.



🧩 Architectural Overview

The architecture employs a microservices-lite approach, containerized via Docker Compose, to decouple high-latency operations (data persistence and logging) from the primary request/response cycle.

1️⃣ Components Breakdown

ComponentTechnologyPrimary RoleRationaleWeb ServerDjango + Django Rest Framework (DRF) + GunicornRequest ingress, validation, immediate response generation, and task dispatch.Provides robust web framework capabilities and efficient WSGI serving.Primary DatabasePostgreSQLAuthoritative source of truth for user registrations (phone numbers, timestamps, confirmation status).Ensures ACID compliance for critical transactional data.Logging DatabaseMongoDBHigh-throughput, schema-flexible storage for request metadata, IP tracking, and audit trails.Decoupled storage optimized for write-heavy, eventual consistency workloads, adhering to SRP.Task Queue BrokerRabbitMQMessage broker responsible for reliably queuing tasks dispatched by Django to Celery workers.Mature, reliable broker supporting complex routing and persistence of messages.Asynchronous WorkersCeleryExecutes long-running or background tasks, primarily data persistence to PostgreSQL and MongoDB.Allows the web layer to remain unblocked.Result Backend/CacheRedisStores the state and results of Celery tasks and provides a high-speed cache layer (e.g., for rate limiting).Essential for Celery task monitoring and extremely fast session/cache access.Monitoring DashboardFlowerWeb-based interface for monitoring, inspecting, and managing Celery tasks and workers in real time.Essential for observability and debugging production task flows.OrchestrationDocker ComposeDefines, runs, and links all services, managing networking, volumes, and startup order.Ensures environmental parity between development, staging, and production deployment contexts.



⚙️ Core Principles in Detail

Single Responsibility Principle (SRP)

The application logic is strictly partitioned to prevent cross-contamination of responsibilities:





Web Layer (views.py): Only responsible for HTTP request handling, input validation (e.g., phone number format validation using complex Regular Expressions), session management (if applicable), and dispatching the asynchronous trigger using .delay(). It must never block waiting for database responses.



Persistence Layer (tasks.py): Dedicated exclusively to business logic execution:





Validation re-check (optional, defensive programming).



PostgreSQL insertion via Django ORM (transactional commitment).



MongoDB logging via decoupled utility functions.



Logging Utilities (logs/utils.py): Contains the specific low-level implementation details for connecting to MongoDB and inserting documents. This keeps the Celery task clean and unaware of MongoDB specifics, allowing easy swapping of logging backends if needed (e.g., to ELK stack later).

Asynchronous Non-blocking Design

The fundamental design choice is immediate feedback:





User Experience: Upon successful validation of the request payload (e.g., phone number format), the API responds immediately with an HTTP 202 Accepted. This signals to the client that the request has been received and is being processed, minimizing perceived latency.



Task Dispatch: The call looks like:

from landing.tasks import save_phone_async
# ... validation passes ...
task = save_phone_async.delay(phone_number, metadata)
return Response({"task_id": task.id, "status": "Processing"}, status=status.HTTP_202_ACCEPTED)




Worker Execution: The Celery worker picks up the message from RabbitMQ and handles the subsequent, time-consuming I/O operations (network calls to DBs).

Dual Database Strategy

This strategy addresses conflicting data persistence requirements:





PostgreSQL (The Source of Truth): Used for storing user phone numbers. This requires data integrity, uniqueness constraints (to prevent duplicate registrations), and transactional consistency, which SQL excels at.





Schema Focus: Structured, normalized data.



MongoDB (The High-Volume Log Store): Used for capturing transient request metadata (IP address, User-Agent, Referrer URL, UUID). This data is write-heavy, does not require transactional joins, and benefits from flexible schemas common in logs. Storing this in PostgreSQL would slow down the core user registration process significantly due to heavy logging transactions.



🚀 Processing Flow: Step-by-Step Transaction

This details the life cycle of a single incoming registration request:

Step 1: Ingress and Initial Validation (Django/Gunicorn)
A client sends an HTTP POST request to /api/register/ carrying the payload, often including identifying headers.

Step 2: Payload Validation
The Django view or DRF serializer rigorously validates the phone_number field. The validation utilizes a sophisticated Regular Expression tailored to the specific national format requirements: $$ \text{Phone Number Validation Regex: } \hat{}0\d{10}$ $$ This pattern ensures the number starts with '0' followed by exactly 10 digits (total 11 digits). If validation fails, an immediate 400 Bad Request is returned.

Step 3: Metadata Extraction
Key request context data is harvested from the HTTP request object:





request_id: A newly generated UUID (e.g., uuid.uuid4()) is crucial for end-to-end tracing.



ip_address: Extracted, often requiring peering through proxy headers (e.g., X-Forwarded-For).



referrer: The originating URL.

Step 4: Asynchronous Task Dispatch
If validation succeeds, the view delegates the heavy lifting:

from landing.tasks import save_phone_async
task_id = save_phone_async.delay(phone_number, request_id, ip_address, referrer)


The .delay() method serializes the arguments and sends a message containing the task name (landing.tasks.save_phone_async) and parameters onto the RabbitMQ queue designated for standard priority tasks.

Step 5: Immediate Response
The Django server returns HTTP 202 Accepted immediately to the client. The response body confirms receipt and provides the task_id for potential future polling (if polling mechanism is implemented).

Step 6: Broker Transmission (RabbitMQ)
RabbitMQ receives the message and reliably queues it, ensuring persistence even if workers are momentarily down.

Step 7: Worker Execution (Celery)
A listening Celery worker pulls the message from RabbitMQ. The worker then executes save_phone_async: a. PostgreSQL Persistence: The worker attempts to create or update the user record in PostgreSQL using Django ORM. This step is wrapped in a transaction. If successful, PostgreSQL commits the record. b. MongoDB Logging: Concurrently (or immediately after SQL success), the worker calls the dedicated utility to log the full metadata package (including the now-linked PostgreSQL ID, if available) into the MongoDB collection.

Step 8: Result Backend Update (Redis)
Celery updates the task status (e.g., SUCCESS, FAILURE) in Redis, which Flower reads for dashboard display.



🧠 Networking & Container Topology (Docker Compose)

Docker Compose is utilized to create a dedicated, isolated network environment, ensuring services communicate reliably using container names rather than unstable host IP addresses.

Internal Network Name: backend_network (Defined in docker-compose.yml)

Service Name (Hostname)Host Port Mapping (External Access)Dependenciesweb8000 (e.g., proxied by Nginx/ArvanCloud)rabbitmq, postgres, redisworkerNone (Internal access only)rabbitmq, postgres, mongodbrabbitmq5672 (Broker), 15672 (Management UI)Noneredis6379Nonepostgres5432Nonemongodb27017Noneflower5555redis (for task results)

Service Communication:





web connects to PostgreSQL via postgres:5432.



web connects to RabbitMQ via rabbitmq:5672 to publish task messages.



worker connects to RabbitMQ via rabbitmq:5672 to consume tasks.



🔍 Reliability & Fault Tolerance

Robustness is built into the startup sequence and connection handling:





Startup Sequencing (depends_on): docker-compose.yml explicitly uses depends_on for services that must be running before dependents start attempting connections.



Health Checks: Critical services (PostgreSQL, RabbitMQ) include standard Docker healthcheck definitions to ensure they are not only running but ready to accept connections before dependent services proceed past the initial wait stage.



Connection Resilience (Celery/Kombu):





Celery workers are configured with retries and exponential backoff for connection failures to RabbitMQ (kombu.exceptions.OperationalError).



Configuration must use container names (RABBITMQ_HOST: rabbitmq) instead of localhost or 127.0.0.1.



Database Readiness Scripts: Custom entrypoint scripts (entrypoint-postgres.sh) are implemented for PostgreSQL. These scripts use pg_isready loop checks to confirm the database instance is fully initialized and accepting connections before allowing the Django application container to start its Gunicorn processes.



🔐 Security & Hardening

Security is addressed at the network, application, and monitoring layers:





Network Isolation: All services reside on the private backend_network. Only the web service is exposed externally (typically through a reverse proxy like Nginx or a CDN). Databases and brokers are inaccessible directly from the external internet.



Monitoring Access Control:





Flower: Requires authentication. A specific FLOWER_USER and FLOWER_PASSWORD are injected via environment variables (.env) and used in the Flower startup command.



Mongo Express: If deployed, it is also protected via basic authentication, restricting access to administrators only.



Application Security (Django): Standard Django security features are enforced:





Strict Cross-Origin Resource Sharing (CORS) configuration in settings.py to only allow the specific frontend domain(s).



Implementation of secure headers (HSTS, X-Content-Type-Options, etc.) via middleware.



Request Tracking: The mandatory use of UUIDs for every request ensures that subsequent audits or support lookups can track the entire lifecycle of a single user submission across Django logs, RabbitMQ queues, and both database records.



📈 Scalability Strategy

Scalability focuses on horizontally increasing the capacity of the bottlenecks, which are typically the web ingress and the asynchronous processing layer.





Web Tier Scaling (Gunicorn): The number of Gunicorn workers (--workers) is set based on CPU core count of the host environment, tuned for I/O efficiency. This tier is stateless regarding persistence, allowing simple horizontal scaling behind a load balancer (Nginx, or external CDN/WAF like ArvanCloud).



Asynchronous Processing Scaling (Celery): This is the most critical scaling vector.





We can spin up multiple worker containers independently.



Celery workers can be configured to use different concurrency settings (e.g., using Gevent pool for high I/O tasks) to maximize throughput.



Caching and Rate Limiting (Redis): Redis is used to implement short-term, high-speed rate limiting on the Django web tier (e.g., blocking IPs attempting more than 10 submissions per minute). This prevents the Celery/DB pipeline from being overwhelmed by abusive traffic, protecting database stability.



📊 Observability

Visibility into the decoupled components is essential for debugging production issues.





Flower Dashboard: Accessed via http://localhost:5555 (internally mapped). This provides real-time visibility into:





Worker health and load.



Queued task counts (RabbitMQ latency check).



Task history (success/failure rates, execution times).



MongoDB Visualization: Via Mongo Express (or direct Mongo CLI on port 8081), administrators can immediately verify that log entries are being created and inspect the structure of the logged metadata associated with a specific request_id.



Application Logging: Gunicorn and Django application logs are directed to stdout/stderr within their containers. This facilitates collection by standard container logging drivers (e.g., Docker logs) for real-time tracing during deployment or debugging sessions.



🧩 Lessons Learned (Operational Wisdom)

Experience gained during the development and testing phases highlights crucial operational details:





Environment Consistency: Strict enforcement of environment variable parity. A common failure mode was misconfigured DB credentials in the worker service's .env file compared to the web service's, leading to phantom connection failures that were difficult to debug until configuration drift was identified.



Network Hostnames: Never use localhost or 127.0.0.1 when defining connections between services within a Docker Compose network. Services must resolve each other using their defined container names (e.g., postgres, rabbitmq).



Base Image Optimization: Utilizing minimal base images (e.g., python:3.12-slim-bookworm) significantly reduces container size, speeds up build times, and inherently reduces the attack surface area compared to full OS images.



Task Idempotency: For any task that updates critical state (like the PostgreSQL write), idempotency checks should be considered, especially given the potential for message redelivery by RabbitMQ under network partition events.



🏁 Conclusion

This architecture provides a high-performance, durable solution for managing high-volume traffic on a critical landing page. By fully embracing asynchronous processing via Celery and RabbitMQ, decoupling logging to MongoDB, and leveraging PostgreSQL for transactional integrity, the system achieves immediate user feedback while guaranteeing that every valid registration request is reliably persisted, logged, and fully traceable via unique request identifiers. This separation of concerns ensures that the system can scale the high-throughput logging layer independently of the core transactional database operations.
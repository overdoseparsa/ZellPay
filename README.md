# ZellPay
ZellPay Accounting System

# Payment Service

<h4 align="center">A clean-architecture based Payment Service inspired by Parloa-style system design.</h4>

<p align="center">
  <img src="https://img.shields.io/badge/tests-pytest-brightgreen" />
  <img src="https://img.shields.io/badge/python-3.11-blue" />
</p>

<p align="center">
  <a href="#project-setup">Project Setup</a> •
  <a href="#endpoints">Endpoints</a> •
  <a href="#system-design">System Design</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#libraries">Libraries</a> •
  <a href="#future-improvements">Future Improvements</a>
</p>

---

## Project Setup

### User Setup

```bash
docker-compose up -d
```

### Developer Setup

1. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run tests

```bash
pytest
```

---

## Endpoints

* `/health` : Health check endpoint
* `/payments` :

  * POST: Create a payment transaction
* `/payments/{transaction_id}` :

  * GET: Retrieve payment status

(gRPC endpoints are defined under `grpc/` for internal service communication.)

---

## System Design

The system follows an asynchronous-first design similar to Parloa's architecture philosophy.

### User Interaction

Clients interact via HTTP or gRPC interfaces. The API layer remains thin and delegates all business logic to services.

### Payment Gateways & Verification

* Gateway integrations (Stripe, Mock, etc.) are isolated under `app/gateways`
* Verification logic is handled asynchronously and can be extended independently

### Messaging & Async Flow

Although currently synchronous, the design supports:

* Event-based processing
* Message broker integration
* Async verification pipelines

This ensures scalability and clear separation of concerns.

---

## Architecture

This project follows **Clean Architecture** principles:

1. **Framework Independence** – Business logic is decoupled from FastAPI / gRPC
2. **Testability** – Core logic is fully testable without infrastructure
3. **UI Independence** – HTTP or gRPC can be swapped without affecting domain
4. **Database Independence** – Storage can change without business impact

### Project Structure

```ini
app/
├── domain/
│   └── transaction/
│       ├── entities/
│       │   └── transaction.py
│       ├── value_objects/
│       │   ├── money.py
│       │   ├── currency.py
│       │   └── authority_code.py
│       ├── services/
│       │   └── transaction_service.py
│       ├── events/
│       │   └── transaction_created.py
│       ├── repositories/
│       │   └── transaction_repository.py
│       └── exceptions.py
│
├── application/
│   └── transaction/
│       ├── commands/
│       │   └── create_transaction.py
│       ├── handlers/
│       │   └── create_transaction_handler.py
│       └── dto.py
│
├── infrastructure/
│   ├── persistence/
│   │   ├── postgres/
│   │   │   └── transaction_repository.py
│   ├── cache/
│   │   └── redis_transaction_cache.py
│   ├── gateways/
│   │   └── zarinpal_client.py
│   └── config/
│       └── settings.py
│
├── interfaces/
│   ├── http/
│   │   └── transaction_controller.py
│   └── cli/
│
├── shared/
│   ├── logging.py
│   └── exceptions.py
│
└── main.py

```

### Clean Architecture Mapping

* **Entities**: `app/models`
* **Use Cases**: `app/services`
* **Interface Adapters**: `gateways`, `repositories`
* **Frameworks & Drivers**: FastAPI, gRPC, database drivers

---

## Libraries

* **FastAPI** – HTTP API framework
* **gRPC** – Internal service communication
* **PyTest** – Testing framework
* **Pydantic** – Data validation

---

## Future Improvements

1. **Async Message Broker**

   * Introduce Kafka / Redis Streams for payment events

2. **Unit of Work + Rollback**

   * Transactional consistency across gateways

3. **Gateway Sandbox Testing**

   * Contract tests for external payment providers

4. **Observability**

   * Structured logging & tracing (OpenTelemetry)

5. **Higher Test Coverage**

   * Especially around failure scenarios & retries

---

### Notes

This README intentionally mirrors the structure and clarity of the Parloa assignment while being adapted to the current payment-service codebase.


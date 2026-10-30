# MiniDash — Food Delivery REST API

**Course:** CSCI-665 Software Engineering  
**Project:** Ship a Feature with an AI Pair  
**Selected Feature:** Track B — Group Orders

## Project Overview

MiniDash is a food delivery REST API developed using Python, FastAPI, and SQLite. It supports browsing restaurants and menus, creating and tracking normal food orders, and collaborating on group orders.

For Track B, I implemented a Group Orders feature that allows a host to create a shared food order, invite participants using a share code, manage individual food selections, and check out the completed group order.

The project was developed incrementally using AI-assisted programming, manual code review, automated testing, and Git commits.

## Technologies

- Python 3.13
- FastAPI — REST API framework
- SQLite — Database
- Pydantic — Request validation
- Uvicorn — Development server
- pytest — Automated testing
- HTTPX / FastAPI TestClient — API integration testing

## Features

### Baseline MiniDash

- List available restaurants.
- Retrieve a restaurant's menu.
- Create normal food orders.
- Retrieve orders and their items.
- Update order statuses.

### Track B — Group Orders

- Create a group order for a selected restaurant.
- Generate a unique eight-character share code.
- Allow participants to join using the share code.
- Limit each group to ten members, including the host.
- Issue private member credentials and store their hashes.
- Allow members to add and remove their own food items.
- Reject items belonging to a different restaurant.
- Calculate individual food subtotals.
- Split a fixed $15.95 delivery fee evenly, distributing remainder cents deterministically.
- Allow only the host to lock the group order.
- Prevent joining or modifying locked orders.
- Detect two-hour inactivity expiration for open groups.
- Allow the host to check out a locked group order.
- Convert group items into a normal MiniDash order using a database transaction.
- Prevent duplicate checkout.

## Installation

Clone the repository:

```bash
git clone https://github.com/DennisG8153/CSCI665-MiniDash.git
cd CSCI665-MiniDash
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

**Windows Command Prompt:**

```cmd
.venv\Scripts\activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

## Database Setup

MiniDash uses SQLite for its database. The database file, `minidash.db`, is created locally and is excluded from Git version control.

After installing the dependencies, initialize the database tables:

```bash
python -c "from src.repository.schema import create_tables; create_tables()"
```

Then populate the database with five example restaurants and 15 menu items:

```bash
python -m src.repository.seed
```

The seed script is intended for a newly initialized database. It skips inserting restaurants or menu items when records already exist in their respective tables.

Once these commands finish, the MiniDash API is ready to run.

## Running the API

From the project's root directory, with the virtual environment activated, run:

```bash
python -m uvicorn src.main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

FastAPI's Swagger interface allows API requests to be tested directly in the browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/restaurants` | List restaurants |
| GET | `/restaurants/{id}/menu` | View a restaurant menu |
| POST | `/orders` | Create a normal order |
| GET | `/orders/{id}` | Retrieve a normal order |
| PATCH | `/orders/{id}/status` | Update an order status |
| POST | `/group-orders` | Create a group order |
| POST | `/group-orders/{share_code}/join` | Join a group |
| POST | `/group-orders/{share_code}/items` | Add a food item |
| DELETE | `/group-orders/{share_code}/items/{item_id}` | Remove an owned food item |
| GET | `/group-orders/{share_code}/summary` | View group totals |
| POST | `/group-orders/{share_code}/lock` | Lock the group (host only) |
| POST | `/group-orders/{share_code}/checkout` | Convert the group into a normal order |

## Group Order Workflow

1. The host creates a group order for a restaurant.
2. MiniDash generates a share code and private host credential.
3. Participants join using the share code and receive individual credentials.
4. Each member adds or removes their own food items.
5. The summary endpoint calculates food subtotals and delivery-fee shares.
6. The host locks the group to prevent further changes.
7. The host submits a delivery address and checks out.
8. MiniDash creates a normal order, copies the group's items, and marks the group as `CHECKED_OUT`.

### Member Authentication

Protected group operations use the HTTP request header:

```text
X-Member-Credential: <member's private credential>
```

Member credentials should be treated as private. Only credential hashes are stored in SQLite.

### Delivery-Fee Calculation

The delivery fee is fixed at **1,595 cents ($15.95)**.

The fee is divided using integer arithmetic to avoid floating-point rounding errors. When the amount cannot be divided evenly, remaining cents are assigned in ascending member-ID order.

For three participants:

| Member | Delivery-fee share |
|---|---|
| Member 1 | $5.32 |
| Member 2 | $5.32 |
| Member 3 | $5.31 |
| **Total** | **$15.95** |

## Running Automated Tests

From the repository root:

```bash
python -m pytest tests/ -v
```

For a shorter result:

```bash
python -m pytest tests/ -q
```

**Latest local test result:** 69 passed.

The test suite covers database constraints, group creation, joining, item ownership, delivery-fee calculations, locking, expiration, checkout, database rollback, and baseline order operations.

Tests use temporary SQLite databases to avoid modifying the normal application database.

## Project Documentation

Additional project documentation is available in:

- `docs/requirements.md` — Functional requirements and acceptance criteria.
- `docs/design.md` — Architecture, data model, and design decisions.
- `docs/tasks.md` — Implementation task breakdown.
- `AI_Log.md` — AI-assisted development interactions, code review, and verification.

## Design Decisions and Limitations

- SQLite is used for persistence.
- Database write transactions protect critical group operations.
- Member credentials are hashed before storage.
- Monetary amounts are calculated in integer cents.
- The delivery fee is fixed rather than dynamically calculated.
- Menu prices are read at checkout; the group-item table does not store historical price snapshots.
- Expiration is evaluated when relevant API operations are performed, rather than by a background scheduler.
- The order-status endpoint validates status names but does not enforce a strict status-transition sequence.

## Development Process

The project was implemented across seven Group Orders development slices, with separate Git commits and automated testing.

AI assistance was used to help develop implementation ideas, review code, identify errors, and design tests. Generated suggestions were reviewed and adjusted before being incorporated into the project.

Details are recorded in `AI_Log.md`.
# Zorvyn Finance Backend API

A high-performance, production-ready backend built for the Zorvyn Finance Dashboard. It provides a robust foundation for managing financial records, analyzing trends, and enforcing strict role-based access control (RBAC).

## 🚀 Tech Stack

*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
*   **Database**: MongoDB
*   **ODM**: [Beanie](https://beanie-odm.dev/) (Asynchronous ODM utilizing Pydantic)
*   **Authentication**: JWT (JSON Web Tokens) with strictly typed OAuth2 flows
*   **Security**: bcrypt password hashing, `SlowAPI` application-level rate limiting
*   **Testing**: Pytest (Async) + HTTPX

---

## ⚙️ Setup Process

### Option 1: Docker (Recommended)
The easiest way to run the application is via Docker Compose, which automatically provisions both the FastAPI server and a local MongoDB instance.

1. Ensure **Docker Desktop** is running.
2. In the project root (`finance_backend`), run:
   ```bash
   docker compose up --build -d
   ```
3. The API will be available at `http://localhost:8000`.

### Option 2: Local Python Environment
If you prefer running it locally without Docker:

1. You must have a MongoDB instance running locally (port `27017`) or configure the `MONGO_URI` inside `.env` to point to a MongoDB Atlas cluster.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## 📖 API Explanation & Documentation

All endpoint interactions are strictly typed and documented automatically via OpenAPI. Once the server is running, you can explore the endpoints interactively:

*   **Swagger Interactive UI:** `http://localhost:8000/docs`
*   **ReDoc Static UI:** `http://localhost:8000/redoc`

### Sub-Modules
1. **Authentication (`/api/v1/auth`)**: Handles registration and login.
2. **Records (`/api/v1/records`)**: Full CRUD functionality for financial data with extensive pagination (`page`, `page_size`) and search/filter support (`$regex` matching). 
3. **Dashboard (`/api/v1/dashboard`)**: Analytics endpoints (`/summary`, `/category-breakdown`, `/monthly-trends`). Calculates heavily aggregated totals directly in the database.
4. **Users (`/api/v1/users`)**: Admin-only user management (promote, demote, deactivate).

### 📬 Postman Collection
For easy API assessment, a fully documented Postman Collection is located at:
`../postman/Zorvyn_Finance_API.postman_collection.json`
*Note: The collection contains a pre-request script that automatically saves your JWT into your Postman environment upon a successful `/login`.*

---

## 🧠 Assumptions Made

1. **Auto-Admin Promotion**: It is assumed that the very first user registering in the newly initialized system is the system administrator. Subsequent registrants default to `viewer` status until manually promoted.
2. **Audit Over Deletion**: It is assumed that in a financial context, data integrity is paramount. Records are never destroyed; they are "soft-deleted" and hidden to preserve auditing capabilities.
3. **Currency Abstraction**: The `amount` field operates as an agnostic `float`. It is assumed the frontend manages explicit formatting/currency handling based on the user's locale.
4. **IP-Based Rate Limiting**: Due to the stateless nature of JWTs, rate limits (e.g. 5 limits/minute on logins) are currently tracked per IP address rather than by user session. 

---

## ⚖️ Tradeoffs Considered

*   **MongoDB Aggregations vs. Application-Level Math**: 
    Computing the dashboard analytics (like monthly trends or total expenses) is done entirely at the database level via MongoDB Aggregation Pipelines instead of fetching all records and doing the math in Python. *Tradeoff*: Constructing `$group` and `$cond` pipelines in MongoDB syntax is slightly more complex to read/maintain than pure Python lists, but vastly improves memory efficiency and network latency.
*   **Beanie ODM vs. Raw PyMongo**: 
    We utilized Beanie ODM. *Tradeoff*: Adding an ODM abstraction layer adds a tiny amount of query overhead compared to writing completely raw PyMongo queries. We traded this negligible latency for the massive benefit of strict Pydantic type validation to prevent malformed data from ever touching the database.
*   **Soft Deletion Checks**: 
    Because we used Soft Deletion, *every* default query in the codebase requires a forced parameter: `Record.is_deleted == False`. We traded slight development overhead (the risk of forgetting to query for this parameter) to permanently protect financial data.

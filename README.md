# Open Forum API

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) 

A robust FastAPI backend designed to model an internal enterprise application for tracking walks and feedback, featuring user authentication and role-based concepts. This project utilizes local database authentication for ease of setup and review.

---

## ✨ Features

* **User Authentication:** Secure login using username/password with JWT bearer tokens.
* **User Management:** Basic user model with roles, regions, and sites.
* **Walk Management:** CRUD operations for creating, retrieving, updating, and archiving walks.
* **Feedback Management:** CRUD operations for creating, retrieving, updating, archiving, and moving feedback between walks.
* **Tag & Comment System:** (If implemented) Models for tagging feedback and adding comments.
* **Role-Based Access Control (RBAC):** (If implemented) Authorization checks based on user roles.
* **Database Seeding:** Automatically populates the database with realistic fake data for demonstration.
* **Dockerized:** Fully containerized using Docker and Docker Compose for easy setup and deployment.
* **Testing:** Comprehensive unit and integration tests using `pytest`.
* **Type Hinting & Validation:** Strong typing with Pydantic and `mypy` checking.

---

## 🛠️ Technology Stack

* **Backend Framework:** FastAPI
* **Database ORM:** SQLAlchemy
* **Database:** PostgreSQL (for production/Docker), SQLite (for testing)
* **Data Validation:** Pydantic
* **Authentication:** JWT Tokens (local), Password Hashing (`pwdlib`)
* **Package Management:** UV
* **Containerization:** Docker, Docker Compose
* **Testing:** Pytest
* **Linting/Formatting:** Ruff (Optional, but recommended)
* **Type Checking:** Mypy

---

## 🚀 Getting Started

### Prerequisites

* Docker & Docker Compose installed ([Docker Desktop](https://www.docker.com/products/docker-desktop/))
* Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git https://github.com/blu371ck/Open-Forum-API.git
    cd Open-Forum-API
    ```

2.  **Environment Variables:**
    * Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    * Review and **edit the `.env` file**. While defaults might work for local Docker setup, ensure variables like `SECRET_KEY` are set. The `DATABASE_URL` should match the one used in `docker-compose.yml` (e.g., pointing to the `db` service).

3.  **Build and Run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    * The `--build` flag ensures images are built the first time or if the Dockerfile changes.
    * This command will:
        * Build the FastAPI application image.
        * Start the PostgreSQL database service.
        * Start the FastAPI application service.
        * **(Wait for seeding)** The application container should automatically run the `seed.py` script upon starting (check your `docker-entrypoint.sh` or `Dockerfile` CMD/ENTRYPOINT).

---

## ▶️ Running the Application

* Once `docker-compose up` is running, the API should be accessible at `http://localhost:8000` (or the port specified in your `docker-compose.yml`).
* Interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
* Alternative documentation (ReDoc) is available at `http://localhost:8000/redoc`.

---

## 🧪 Running Tests

* Ensure the Docker containers are **not** running (`docker-compose down` if they are). Tests use their own in-memory database configuration via `pyproject.toml`.
* Run tests using `uv`:
    ```bash
    uv run pytest
    ```
* To run tests with coverage:
    ```bash
    uv run pytest --cov=app --cov-report=term-missing
    ```

---

## 🌱 Seeding the Database

* The database is automatically seeded when the application container starts via Docker Compose.
* If you need to re-seed the database manually (e.g., after clearing volumes), you can often run the seed script inside the running container or stop the containers, remove the database volume, and start them again.
    * *Example (if container is running):* `docker-compose exec app uv run python seed.py` (adjust service name `app` and script path if needed).

---

## 🔑 Default Login Credentials

The seeding script creates multiple users. Use the following credentials to log in via the `/api/v1/users/auth` endpoint:

* **Developer Account:**
    * **Username:** `(Check console output during docker-compose up for the specific email)`
    * **Password:** `password123`
* **(Optional: Add other example roles if useful)**
    * **Manager Example Username:** `(Find one from seed output or query DB)`
    * **Password:** `password123`

---

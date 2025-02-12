# Expense Tracker API

The Expense Tracker API is a backend service that enables users to manage their personal finances by tracking and categorizing their expenses.

## Features

- User authentication and session management with JWT-based system.
- Expense management with CRUD operations.
- Expenses filtered by time periods, date range, or categories.
- Handle large datasets with limit/offset and sort by fields.

## Installation

1. Clone the repository:

```bash
$ git clone https://github.com/dangvonguyen/expense-tracker-api.git
$ cd expense-tracker-api
```

2. Install dependencies using `uv`:

```bash
$ uv sync
```

3. Activate the virtual environment:

```bash
$ source .venv/bin/activate
```

4. Initialize the database:

```bash
$ bash ./scripts/prestart.sh
```

## Usage

1. Start the FastAPI server:

```bash
$ fastapi run app/main.py
```

2. The API will be available at `http://localhost:8000`

3. Access the interactive API documentation at `http://localhost:8000/docs`

## Acknowledgments

This project idea is inspired by the [Expense Tracker API project](https://roadmap.sh/projects/expense-tracker-api) from roadmap.sh.

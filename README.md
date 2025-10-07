# Koha Endpoint Bridge

Expose Pastel (or any ODBC-accessible) student records as JSON over HTTP for easy consumption from Koha or other downstream systems.

## Features
- Pulls student data via configurable SQL query.
- Presents both raw records and Koha-ready patron payloads.
- Optional filters (`active_only`) and diagnostics (`include_raw`, `strict`).
- `.env` driven configuration suitable for Windows deployment.

## Prerequisites
- Python 3.11+ (tested with CPython on Windows).
- ODBC driver installed for your source database (e.g. *ODBC Driver 17 for SQL Server*).
- Access credentials or DSN for the database view/table containing student information.

## Setup
1. Clone or copy this project onto the Windows host that can reach the database.
2. Optionally create and activate a virtual environment:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create a `.env` file:
   ```powershell
   copy .env.example .env
   ```
   Adjust connection details, SQL query, and Koha defaults to match your environment.

## Running the service
Run the FastAPI application with Uvicorn:

```powershell
python -m uvicorn koha_sync.app:app --host 0.0.0.0 --port 8100
```

Or use the built-in launcher:

```powershell
python -m koha_sync.app
```

### Key endpoints
- `GET /health` – readiness probe.
- `GET /students?active_only=true` – raw records returned from your SQL query.
- `GET /koha/patrons?include_raw=true` – Koha payloads (optionally wraps raw source rows).
- `GET /koha/patrons/{reg_no}` – single Koha payload for a specific student.

### Example request
```powershell
curl http://localhost:8100/koha/patrons?active_only=true
```

## Configuration notes
- `DB_CONNECTION_STRING` is the most portable option; alternatively supply `DB_DSN` + `DB_USERNAME` + `DB_PASSWORD`.
- `STUDENTS_QUERY` must include at least `reg_no`, `first_name`, and `surname`. Optional columns (`email`, `phone`, `course`, `level`, `faculty`) are consumed when present.
- Use `ACTIVE_WHERE_CLAUSE` to append additional filters when `active_only=true`.
- `KOHA_STATIC_ATTRIBUTES` lets you append constants such as `faculty=Commerce,year=2024`.

## Running as a Windows service (optional)
You can use [NSSM](https://nssm.cc/) to keep the bridge running in the background:
1. Install NSSM (`choco install nssm` or download manually).
2. Register the service:
   ```powershell
   nssm install KohaBridge "C:\Path\to\python.exe" "C:\Path\to\koha_enpoint\launch.cmd"
   ```
3. Create `launch.cmd` to activate your virtualenv and start Uvicorn:
   ```cmd
   @echo off
   call C:\Path\to\koha_enpoint\.venv\Scripts\activate.bat
   python -m uvicorn koha_sync.app:app --host 0.0.0.0 --port 8100
   ```
4. `nssm start KohaBridge`

## Next steps
- Wire the consumer (e.g. Koha sync job) to read from `http://server:8100/koha/patrons`.
- Add authentication (API key or Windows firewall rules) if the endpoint is exposed beyond the local network.

# File: README.md

# Company FastAPI Server

Professional FastAPI server with comprehensive documentation and CORS support.

## Features

✅ **Health Check Endpoints**: Basic and detailed health monitoring  
✅ **Swagger Documentation**: Auto-generated API docs at `/docs`  
✅ **CORS Configuration**: Ready for frontend integration  
✅ **Professional Structure**: Organized, scalable codebase  
✅ **Environment Configuration**: Easy deployment settings

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Development Server

```bash
# Method 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Using the run script
python run_server.py
```

### 3. Verify Installation

- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **API Info**: http://localhost:8000/info

## API Endpoints

| Endpoint                  | Method | Description                |
| ------------------------- | ------ | -------------------------- |
| `/`                       | GET    | Redirects to documentation |
| `/docs`                   | GET    | Swagger UI documentation   |
| `/api/v1/health`          | GET    | Basic health check         |
| `/api/v1/health/detailed` | GET    | Detailed health check      |
| `/info`                   | GET    | Application information    |

## Configuration

Create a `.env` file for environment-specific settings:

```env
APP_NAME=Your Company API
APP_VERSION=1.0.0
DEBUG=false
ALLOWED_ORIGINS=["http://localhost:3000","https://yourfrontend.com"]
```

```

## Verification Checklist

- [ ] Server starts without errors
- [ ] Swagger UI accessible at `/docs`
- [ ] Health check returns 200 OK
- [ ] CORS headers present in responses
- [ ] API documentation auto-generated

---

# File: .env.example

# Copy this file to .env and modify as needed

# Application Settings

APP_NAME=Company FastAPI Server
APP_VERSION=1.0.0
APP_DESCRIPTION=Professional FastAPI server with comprehensive documentation
DEBUG=false

# CORS Settings (JSON array format)

ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8080","http://localhost:4200"]

# API Settings

API_V1_PREFIX=/api/v1

---

# File: run_server.py

#!/usr/bin/env python3
"""
Development server runner for FastAPI application
"""

import uvicorn
from app.config import settings

if **name** == "**main**":
print(f"Starting {settings.app_name} v{settings.app_version}")
print(f"Debug mode: {settings.debug}")
print("Server will be available at:")
print(" • Swagger UI: http://localhost:8000/docs")
print(" • Health Check: http://localhost:8000/api/v1/health")
print(" • API Info: http://localhost:8000/info")
print("\nPress Ctrl+C to stop the server")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )

---

# File: .gitignore

# Python

**pycache**/
_.py[cod]
_$py.class
_.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/  
wheels/
_.egg-info/
.installed.cfg
\*.egg
Test

# Environment

.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE

.vscode/
.idea/
_.swp
_.swo
\*~

# OS

.DS*Store
.DS_Store?
.*\*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

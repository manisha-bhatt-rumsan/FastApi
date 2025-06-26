# File: README.md

# AI Quiz Generator


## Features

✅ **Health Check Endpoints**: Basic and detailed health monitoring  
✅ **Swagger Documentation**: Auto-generated API docs at `/docs`  
✅ **CORS Configuration**: Ready for frontend integration  
✅ **Professional Structure**: Organized, scalable codebase  
✅ **Environment Configuration**: Easy deployment settings

## Quick Start

### 1. Make sure that python is installed
Version requirements: `python version >= 3.12`

### 1. Create a virtual enviroment :
```bash 
python -m venv env
```

### 2. Activate the environment : 
```bash
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the .env file and store your credentials

```bash 
cp .env.example .env
```

### 5. Run alembic migrations : 

```bash 
alembic upgrade head
```

### 6. Run Development Server

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

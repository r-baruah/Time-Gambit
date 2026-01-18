@echo off
start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
start cmd /k "cd frontend && npm run dev"
echo "Project Started! Backend at port 8000, Frontend at port 3000."
pause

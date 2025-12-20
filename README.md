# Quick Start

```bash
conda create -y --name ETT python=3.11
conda activate ETT
pip install -r requirements.txt
# for development
python manage.py runserver localhost:8000
# for production
pip install uvicorn
uvicorn ETT_backend.asgi:application --reload --host 0.0.0.0 --port 8000
```
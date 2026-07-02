FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Note for Phase 5+: For production deployment, convert this to a multi-stage 
# build (separating wheel compilation from runtime image) to minimize image size.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

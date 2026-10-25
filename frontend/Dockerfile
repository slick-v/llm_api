FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8501
# Railway sets PORT; 8501 is the default for docker-compose.
# BASE_URL_PATH=streamlit serves the app under /streamlit/ (set in docker-compose).
CMD ["sh", "-c", "exec streamlit run app.py \
     --server.port=${PORT:-8501} \
     --server.baseUrlPath=${BASE_URL_PATH:-} \
     --server.address=0.0.0.0 \
     --server.headless=true \
     --browser.gatherUsageStats=false"]

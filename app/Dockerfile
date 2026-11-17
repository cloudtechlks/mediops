FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home mediops
COPY . .
USER mediops
EXPOSE 3000
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${APP_PORT:-3000} --workers 2 --threads 2 --timeout 40 app:app"]
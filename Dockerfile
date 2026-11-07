FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
CMD ["sh","-c","python -m api.init_db && uvicorn api.index:app --host 0.0.0.0 --port ${PORT:-8000}"]
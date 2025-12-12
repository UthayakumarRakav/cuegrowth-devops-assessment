FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system --gid 1002 worker && adduser --system --uid 1002 --ingroup worker worker

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R worker:worker /app
USER worker

EXPOSE 8001

CMD ["python", "main.py"]

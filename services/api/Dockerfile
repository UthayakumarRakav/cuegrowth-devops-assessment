FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system --gid 1001 app && adduser --system --uid 1001 --ingroup app app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip==25.3
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

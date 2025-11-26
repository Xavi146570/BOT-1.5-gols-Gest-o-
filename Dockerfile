# -----------------------------
# 1. BASE IMAGE
# -----------------------------
FROM python:3.10-slim

# -----------------------------
# 2. SYSTEM DEPENDENCIES
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 3. WORKDIR
# -----------------------------
WORKDIR /app

# -----------------------------
# 4. COPY REQUIREMENTS
# -----------------------------
COPY requirements.txt .

# -----------------------------
# 5. INSTALL PYTHON DEPENDENCIES
# -----------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# 6. COPY PROJECT FILES
# -----------------------------
COPY . .

# -----------------------------
# 7. EXPOSE PORT
# -----------------------------
EXPOSE 8000

# -----------------------------
# 8. START COMMAND FOR RENDER
# -----------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

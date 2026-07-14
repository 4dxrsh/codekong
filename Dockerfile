# CodeKong — demo container for review submission.
# Serves the web UI (with the real, committed experiment results, the
# "How It Works" walkthrough, and the Caught Bugs gallery) and can run the
# offline smoke suite. Small, deterministic, and runs anywhere Docker runs.
#
#   docker build -t codekong .
#   docker run --rm -p 5001:5001 codekong        # open http://localhost:5001
#   docker run --rm codekong python tests/smoke_all.py   # -> 9/9
FROM python:3.12-slim

WORKDIR /app

# Install the (small) demo dependencies first for better layer caching.
COPY requirements-demo.txt .
RUN pip install --no-cache-dir -r requirements-demo.txt

# App code + committed results, benchmark, and generated tests.
COPY . .

ENV HOST=0.0.0.0 \
    PORT=5001 \
    PYTHONUNBUFFERED=1

EXPOSE 5001

# Default: serve the web UI. Override to run the tests, e.g.:
#   docker run --rm codekong python tests/smoke_all.py
CMD ["python", "-m", "frontend.app"]

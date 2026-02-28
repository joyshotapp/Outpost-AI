#!/bin/bash
# Script to run Celery worker and beat scheduler

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Factory Insider Celery Worker${NC}"
echo "=================================="
echo ""

# Check if Redis is running
echo -e "${YELLOW}Checking Redis connection...${NC}"
python -c "
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✓ Redis is running')
except Exception as e:
    print(f'✗ Redis error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Redis is not running. Please start Redis first.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Starting Celery Worker...${NC}"
echo "=================================="

# Start Celery worker with multiple concurrency settings
# Options:
# -A: App module
# -l: Log level
# -c: Concurrency (number of worker processes)
# -Q: Queues to consume (comma-separated)
# --time-limit: Hard time limit for tasks (seconds)
# --soft-time-limit: Soft time limit for tasks (seconds)

celery -A app.celery worker \
    -l info \
    -c 4 \
    -Q email,video,analytics,ai,celery \
    --time-limit=1800 \
    --soft-time-limit=1500

echo ""
echo -e "${GREEN}Celery Worker stopped${NC}"

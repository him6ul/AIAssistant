#!/bin/bash

# Quick API testing script

echo "🧪 Testing AI Assistant API..."
echo ""

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "1️⃣  Testing Health Check..."
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "   Response: $HEALTH"
fi
echo ""

# Test 2: Status
echo "2️⃣  Testing Status Endpoint..."
STATUS=$(curl -s "$BASE_URL/status")
if [ ! -z "$STATUS" ]; then
    echo -e "${GREEN}✅ Status endpoint working${NC}"
    echo "   Response: $STATUS"
else
    echo -e "${RED}❌ Status endpoint failed${NC}"
fi
echo ""

# Test 3: Get Tasks
echo "3️⃣  Testing Get Tasks..."
TASKS=$(curl -s "$BASE_URL/tasks")
if [ ! -z "$TASKS" ]; then
    TASK_COUNT=$(echo "$TASKS" | grep -o '"id"' | wc -l | tr -d ' ')
    echo -e "${GREEN}✅ Tasks endpoint working${NC}"
    echo "   Found $TASK_COUNT tasks"
else
    echo -e "${RED}❌ Tasks endpoint failed${NC}"
fi
echo ""

# Test 4: Chat (if jq is available, format nicely)
echo "4️⃣  Testing Chat Endpoint..."
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, this is a test"}')

if echo "$CHAT_RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✅ Chat endpoint working${NC}"
    if command -v jq &> /dev/null; then
        echo "$CHAT_RESPONSE" | jq .
    else
        echo "   Response: $CHAT_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠️  Chat endpoint may need LLM configuration${NC}"
    echo "   Response: $CHAT_RESPONSE"
fi
echo ""

# Test 5: Create Task
echo "5️⃣  Testing Create Task..."
CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task from Script",
    "description": "Created by test script",
    "importance": "low",
    "classification": "do"
  }')

if echo "$CREATE_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✅ Create task working${NC}"
    TASK_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
    echo "   Created task ID: $TASK_ID"
else
    echo -e "${RED}❌ Create task failed${NC}"
    echo "   Response: $CREATE_RESPONSE"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ API Testing Complete!"
echo ""
echo "💡 For more detailed testing, visit:"
echo "   http://localhost:8000/docs"
echo ""


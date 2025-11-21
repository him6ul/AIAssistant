#!/bin/bash

# Verify setup and check for common issues

cd "$(dirname "$0")/.."

echo "🔍 Verifying AI Assistant Setup..."
echo ""

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
    echo "   ✅ Python $PYTHON_VERSION (OK)"
else
    echo "   ❌ Python $PYTHON_VERSION (Need 3.11+)"
fi

# Check virtual environment
echo ""
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment exists"
else
    echo "   ⚠️  Virtual environment not found (run: python3 -m venv venv)"
fi

# Check .env file
echo ""
echo "3. Checking .env file..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    # Check for required variables
    if grep -q "OPENAI_API_KEY" .env && ! grep -q "OPENAI_API_KEY=your_" .env; then
        echo "   ✅ OPENAI_API_KEY configured"
    else
        echo "   ⚠️  OPENAI_API_KEY not configured"
    fi
    
    if grep -q "OLLAMA_BASE_URL" .env; then
        echo "   ✅ OLLAMA_BASE_URL configured"
    else
        echo "   ⚠️  OLLAMA_BASE_URL not configured"
    fi
else
    echo "   ❌ .env file not found (copy from .env.example)"
fi

# Check config file
echo ""
echo "4. Checking config file..."
if [ -f "config/config.yaml" ]; then
    echo "   ✅ config.yaml exists"
else
    echo "   ❌ config.yaml not found"
fi

# Check dependencies
echo ""
echo "5. Checking Python dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
    if python3 -c "import fastapi" 2>/dev/null; then
        echo "   ✅ FastAPI installed"
    else
        echo "   ⚠️  FastAPI not installed (run: pip install -r requirements.txt)"
    fi
    
    if python3 -c "import openai" 2>/dev/null; then
        echo "   ✅ OpenAI installed"
    else
        echo "   ⚠️  OpenAI not installed"
    fi
    
    if python3 -c "import ollama" 2>/dev/null; then
        echo "   ✅ Ollama client installed"
    else
        echo "   ⚠️  Ollama client not installed"
    fi
else
    echo "   ⚠️  Cannot check (virtual environment not found)"
fi

# Check Ollama service
echo ""
echo "6. Checking Ollama service..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama service is running"
    
    # Check for llama3 model
    if ollama list 2>/dev/null | grep -q "llama3"; then
        echo "   ✅ llama3 model installed"
    else
        echo "   ⚠️  llama3 model not found (run: ollama pull llama3)"
    fi
else
    echo "   ⚠️  Ollama service not running (start with: ollama serve)"
fi

# Check directories
echo ""
echo "7. Checking directories..."
mkdir -p data logs
if [ -d "data" ]; then
    echo "   ✅ data/ directory exists"
fi
if [ -d "logs" ]; then
    echo "   ✅ logs/ directory exists"
fi

# Check scripts
echo ""
echo "8. Checking scripts..."
if [ -x "scripts/run_all.sh" ]; then
    echo "   ✅ run_all.sh is executable"
else
    echo "   ⚠️  run_all.sh is not executable (run: chmod +x scripts/*.sh)"
fi

# Check SwiftUI app
echo ""
echo "9. Checking SwiftUI app..."
if [ -d "mac-ui/Sources" ]; then
    echo "   ✅ SwiftUI sources exist"
    if [ -f "mac-ui/Sources/MenuBarApp.swift" ]; then
        echo "   ✅ MenuBarApp.swift exists"
    fi
else
    echo "   ⚠️  SwiftUI sources not found"
fi

echo ""
echo "✅ Setup verification complete!"
echo ""
echo "Next steps:"
echo "1. Configure .env with your API keys"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Start Ollama: ollama serve && ollama pull llama3"
echo "4. Run the system: ./scripts/run_all.sh"


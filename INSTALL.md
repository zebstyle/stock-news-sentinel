# Installation Guide - Stock News Sentinel

This guide provides multiple installation methods to help you get Stock News Sentinel running on your system.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Internet connection

## Method 1: Standard Installation (Recommended)

### Step 1: Upgrade pip and setuptools

```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 2: Install dependencies

```bash
cd stock-news-sentinel
pip install -r requirements.txt
```

**Note:** First installation may take 10-15 minutes as it downloads models and compiles packages.

## Method 2: Install with Pre-built Wheels (If Method 1 Fails)

If you encounter build errors (especially with pandas, numpy, or torch), use pre-built wheels:

### Windows

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install core packages with pre-built wheels
pip install --only-binary :all: numpy pandas

# Then install remaining requirements
pip install -r requirements.txt
```

### Linux/Mac

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install core packages
pip install --only-binary :all: numpy pandas

# Then install remaining requirements
pip install -r requirements.txt
```

## Method 3: Install in Stages (For Troubleshooting)

If you're having issues, install packages in stages:

### Stage 1: Core Dependencies

```bash
pip install streamlit python-dotenv
```

### Stage 2: Data Processing

```bash
pip install numpy pandas
```

### Stage 3: Web Scraping

```bash
pip install beautifulsoup4 requests lxml
pip install selenium webdriver-manager
pip install newspaper3k
```

### Stage 4: Sentiment Analysis

```bash
pip install transformers torch
pip install vaderSentiment textblob
```

### Stage 5: Remaining Packages

```bash
pip install langchain langchain-community langchain-core
pip install APScheduler colorlog configparser
pip install python-dateutil pytz httpx
```

## Method 4: Using Conda (Alternative)

If pip installation fails, try using Conda:

```bash
# Create conda environment
conda create -n stock-sentinel python=3.10
conda activate stock-sentinel

# Install packages via conda where possible
conda install numpy pandas
conda install -c conda-forge beautifulsoup4 requests lxml

# Install remaining via pip
pip install -r requirements.txt
```

## Common Installation Issues

### Issue 1: Build Tools Missing (Windows)

**Error:** "Microsoft Visual C++ 14.0 or greater is required"

**Solution:**
1. Install Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Or use pre-built wheels (Method 2)

### Issue 2: Build Tools Missing (Linux)

**Error:** "error: command 'gcc' failed"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# CentOS/RHEL
sudo yum install python3-devel gcc gcc-c++
```

### Issue 3: Pandas/Numpy Build Failure

**Error:** "Failed to build pandas/numpy"

**Solution:**
```bash
# Use pre-built wheels
pip install --only-binary :all: numpy pandas

# Or install from conda
conda install numpy pandas
```

### Issue 4: Torch Installation Issues

**Error:** Torch installation fails or takes too long

**Solution:**
```bash
# Install CPU-only version (smaller, faster)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue 5: Transformers/FinBERT Model Download

**Error:** Model download fails or times out

**Solution:**
- Ensure stable internet connection
- The FinBERT model (~400MB) downloads on first use
- If download fails, it will retry automatically
- Or use VADER as primary model (no download needed):
  ```properties
  # In config.properties
  primary_sentiment_model=vader
  ```

## Minimal Installation (Core Features Only)

If you want to start with minimal dependencies and add features later:

```bash
# Core only (no sentiment analysis)
pip install streamlit beautifulsoup4 requests pandas

# Add sentiment analysis later
pip install transformers torch vaderSentiment

# Add web scraping enhancements
pip install selenium webdriver-manager newspaper3k
```

## Verify Installation

After installation, verify everything works:

```bash
# Check Python version
python --version  # Should be 3.10+

# Check installed packages
pip list | grep -E "streamlit|pandas|transformers"

# Test import
python -c "import streamlit; import pandas; import transformers; print('All imports successful!')"
```

## Running the Application

Once installed:

```bash
cd stock-news-sentinel
streamlit run app.py
```

The application should open in your browser at `http://localhost:8501`

## Docker Installation (Advanced)

For a containerized installation:

```dockerfile
# Create Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run application
CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t stock-sentinel .
docker run -p 8501:8501 stock-sentinel
```

## Getting Help

If you continue to have installation issues:

1. Check Python version: `python --version` (must be 3.10+)
2. Update pip: `python -m pip install --upgrade pip`
3. Try Method 2 (pre-built wheels)
4. Check system requirements (RAM, disk space)
5. Review error messages carefully
6. Try minimal installation first

## System Requirements

- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 2GB free (for models and dependencies)
- **Python:** 3.10 or higher
- **Internet:** Required for initial setup and news scraping

## Next Steps

After successful installation:

1. Read [QUICKSTART.md](QUICKSTART.md) for configuration
2. Configure `config.properties` with your settings
3. Set up email alerts (Gmail app password)
4. Run your first scan

---

**Made with Bob** 🤖
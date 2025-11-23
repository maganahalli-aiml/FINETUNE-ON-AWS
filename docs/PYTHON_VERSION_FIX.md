# 🔧 Python Version Fix Guide

## ❌ **Problem:** 
```bash
python --version
# Error: xcode-select: Failed to locate 'python', requesting installation of command line developer tools.
```

## ✅ **Solution:**

### **Quick Fix - Use Correct Commands:**
```bash
# ❌ DON'T use: python
# ✅ USE instead:

# System Python (3.9.6)
python3 --version

# Virtual Environment Python (3.14.0) - RECOMMENDED
.venv/bin/python --version

# For your API testing:
.venv/bin/python simple_api_test.py test aws-iam
```

### **Why This Happens:**
- macOS doesn't include a `python` command by default (only `python3`)
- Your virtual environment has Python 3.14.0 
- System has Python 3.9.6
- The `python` command triggers Xcode tools installation prompt

### **✅ Current Working Setup:**
```bash
# System Python
/usr/bin/python3 --version  # Python 3.9.6

# Virtual Environment Python  
.venv/bin/python --version   # Python 3.14.0

# Your API works with venv Python
.venv/bin/python simple_api_test.py test aws-iam
```

### **Optional: Install Xcode Command Line Tools**
If you want the `python` command:
```bash
# Install Xcode command line tools
xcode-select --install

# Then create alias (add to ~/.zshrc)
alias python=python3
```

### **Recommended: Stick with Current Setup**
Your current setup is working perfectly:
- ✅ Virtual environment with Python 3.14.0
- ✅ API testing functional
- ✅ AWS integration working
- ✅ Cost scanning operational

**No need to change anything - just use `.venv/bin/python` for your project!**
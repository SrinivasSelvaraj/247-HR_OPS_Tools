# Quick Installation Guide

## 🚀 Quick Start

### Option 1: Simple Installation (Recommended)

1. **Install Flask (minimum required)**
   ```bash
   pip install flask
   ```

2. **Run the application**
   ```bash
   python run.py
   ```

3. **Open in browser**
   Navigate to `http://localhost:5000`

### Option 2: Full Installation

1. **Install all dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the full application**
   ```bash
   python app.py
   ```

## 🔧 Common Issues and Solutions

### ImportError: cannot import name 'Config' from 'config'
**Solution**: Use the `run.py` script instead, which handles imports automatically.

### ModuleNotFoundError: No module named 'flask'
**Solution**: Install Flask using:
```bash
pip install flask
```

### Missing dependencies for specific tools
**Solution**: Install additional packages as needed:
```bash
# For ID Image Processor
pip install Pillow opencv-python

# For PDF Toolkit
pip install PyPDF2 reportlab

# For full functionality
pip install -r requirements.txt
```

## 📁 Directory Structure
Make sure you're in the correct directory:
```
247-HR_OPS_Tools/
├── app.py
├── run.py              # <-- Use this for easy startup
├── config.py
├── requirements.txt
├── templates/
├── static/
├── tools/
└── utils/
```

## 🌐 Accessing the Application
Once running, access the application at:
- **Home Page**: `http://localhost:5000`
- **ID Processor**: `http://localhost:5000/id-processor`
- **PDF Toolkit**: `http://localhost:5000/pdf-toolkit`
- And other tools...

## 🆘 Need Help?
If you encounter issues:
1. Try the simple installation first
2. Check that you're in the correct directory
3. Make sure all required files are present
4. Use `run.py` instead of `app.py` for startup
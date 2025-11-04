# 🔧 Fix Import Error - Complete Solution

## ❌ The Problem
```bash
ImportError: cannot import name 'Config' from 'config'
```

## ✅ The Solution

### **Option 1: Quick Fix (Recommended)**

1. **Replace your current `app.py` with the fixed version**

   Open your `app.py` file and replace its entire content with this:

```python
from flask import Flask
from config import BaseConfig, config
import logging
import os

def create_app(config_class=None):
    """
    Application factory pattern for Flask app.
    """
    app = Flask(__name__)

    # Determine which config to use
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'development')
        config_class = config.get(env, BaseConfig)

    app.config.from_object(config_class)

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/hr_toolkit.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('HR Operations Toolkit startup')

    # Main route
    @app.route('/')
    def index():
        """
        Renders the main page of the HR Toolkit.
        """
        tools = [
            {
                "name": "ID Image Processor",
                "icon": "fa-solid fa-id-card",
                "description": "Crop candidate Images for ID cards or HRMS either single or bulk.",
                "url": "/id-processor"
            },
            {
                "name": "Complete PDF Toolkit",
                "icon": "fa-solid fa-file-pdf",
                "description": "A complete offline PDF toolkit for all your PDF needs.",
                "url": "/pdf-toolkit"
            },
            {
                "name": "Employee Exit Verifier",
                "icon": "fa-solid fa-person-walking-arrow-right",
                "description": "Instantaneous check candidates exit status and FFS details.",
                "url": "/exit-verifier"
            },
            {
                "name": "Candidate Experience Calculator",
                "icon": "fa-solid fa-calculator",
                "description": "Analyze the candidate work experience of previous companies.",
                "url": "/exp-calculator"
            },
            {
                "name": "Offer Release Tracker",
                "icon": "fa-solid fa-clipboard-check",
                "description": "User friendly Tracker for logging offer releases.",
                "url": "/offer-tracker"
            },
            {
                "name": "Employee ID Availability",
                "icon": "fa-solid fa-magnifying-glass-plus",
                "description": "Check EMP ID availability for EMP ID allocation.",
                "url": "/id-checker"
            },
        ]
        from flask import render_template
        return render_template('index.html', tools=tools)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    # Create necessary directories
    for directory in ['data/uploads', 'data/exports', 'logs']:
        os.makedirs(directory, exist_ok=True)

    app = create_app()
    print("🚀 Starting HR Operations Toolkit...")
    print("📍 Application will be available at: http://localhost:5000")
    print("🔧 Press Ctrl+C to stop the server")
    app.run(debug=True)
```

### **Option 2: Use the Simple Runner**

1. **Install Flask (if not already installed)**
   ```bash
   pip install flask
   ```

2. **Run the simple application**
   ```bash
   python run.py
   ```

### **Option 3: Manual Fix**

Just change line 2 in your `app.py`:

**FROM:**
```python
from config import Config
```

**TO:**
```python
from config import BaseConfig, config
```

And change line 6:

**FROM:**
```python
def create_app(config_class=Config):
```

**TO:**
```python
def create_app(config_class=None):
```

## 🔍 What Was Wrong?

The original code tried to import `Config` from `config.py`, but that class doesn't exist. The actual classes in `config.py` are:
- `BaseConfig`
- `DevelopmentConfig`
- `ProductionConfig`
- `TestingConfig`

## 🚀 After Fix

Run the application:
```bash
python app.py
```

You should see:
```
🚀 Starting HR Operations Toolkit...
📍 Application will be available at: http://localhost:5000
🔧 Press Ctrl+C to stop the server
```

Then open http://localhost:5000 in your browser.

## 📞 Still Having Issues?

1. Make sure you're in the correct directory
2. Check that all files are present (`config.py`, `templates/`, etc.)
3. Try the `run.py` method as fallback
4. Install Flask: `pip install flask`

---

**Quick Test:**
```bash
python -c "from config import BaseConfig; print('✅ Config import works!')"
```

If this prints the success message, your configuration is correct.
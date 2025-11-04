# HR Operations Toolkit

A comprehensive, modular Flask application for HR operations management, featuring six essential tools designed to streamline daily HR tasks and improve efficiency.

## 🚀 Features

### Core Tools
1. **ID Image Processor** - Crop and optimize candidate images for ID cards and HRMS systems
2. **Complete PDF Toolkit** - Merge, split, compress, watermark, and convert PDF files
3. **Employee Exit Verifier** - Verify employee exit status and FFS details
4. **Candidate Experience Calculator** - Analyze and calculate total work experience
5. **Offer Release Tracker** - Track offer releases with status and communication logs
6. **Employee ID Availability** - Check and generate available employee IDs

### Enhanced Features
- 🎨 **Modern UI/UX** - Dark mode support, responsive design, animations
- 🔍 **Search & Filter** - Real-time search, category filtering, sorting options
- 📊 **Analytics Dashboard** - Usage statistics, activity tracking, performance metrics
- 🔒 **Security** - File validation, secure uploads, CSRF protection
- 📱 **Mobile Responsive** - Works seamlessly on all devices
- 🎯 **Easy Navigation** - Breadcrumb navigation, quick access, keyboard shortcuts

## 📋 Requirements

- Python 3.8+
- pip package manager
- Modern web browser

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd 247-HR_OPS_Tools
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy `.env` file and configure your settings:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📁 Project Structure

```
247-HR_OPS_Tools/
├── app.py                     # Main Flask application
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── .gitignore                # Git ignore file
├── README.md                 # Documentation
├── static/                   # Static assets
│   ├── css/
│   │   └── custom.css        # Custom styles
│   ├── js/
│   │   └── main.js          # JavaScript functionality
│   └── images/              # Tool icons and images
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── index.html           # Homepage
│   ├── tools/               # Tool-specific templates
│   │   ├── id_processor.html
│   │   ├── pdf_toolkit.html
│   │   ├── exit_verifier.html
│   │   ├── exp_calculator.html
│   │   ├── offer_tracker.html
│   │   └── id_checker.html
│   ├── components/          # Reusable components
│   │   ├── header.html
│   │   ├── footer.html
│   │   └── help_modal.html
│   └── errors/              # Error templates
│       ├── 404.html
│       └── 500.html
├── tools/                   # Tool implementations
│   ├── __init__.py
│   ├── id_processor.py
│   ├── pdf_toolkit.py
│   ├── exit_verifier.py
│   ├── exp_calculator.py
│   ├── offer_tracker.py
│   └── id_checker.py
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── file_handler.py
│   └── validators.py
└── data/                    # Data storage
    ├── uploads/             # File uploads
    ├── exports/             # Generated files
    └── database.db          # SQLite database
```

## 🔧 Tool Details

### ID Image Processor
- **Features**: Single/bulk upload, face detection, size optimization, multiple formats
- **Supported Formats**: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP
- **Output**: Optimized ID-sized images with optional face detection

### PDF Toolkit
- **Operations**: Merge, split, compress, watermark, convert to images, extract text
- **File Size**: Up to 50MB per PDF
- **Output**: Processed PDFs or ZIP archives for multiple files

### Employee Exit Verifier
- **Features**: Exit status lookup, FFS details, bulk verification
- **Integration**: HR database connectivity (configurable)
- **Reports**: Detailed exit status reports

### Candidate Experience Calculator
- **Features**: Experience gap analysis, total calculation, certificate parsing
- **Input**: Work experience periods with dates
- **Output**: Total experience in years/months with gap analysis

### Offer Release Tracker
- **Features**: Offer logging, status tracking, communication logs
- **Status Types**: Pending, accepted, rejected, withdrawn
- **Notifications**: Email integration (configurable)

### Employee ID Availability
- **Features**: Real-time availability check, pattern generation, bulk allocation
- **Supported Patterns**: EMP####, USER####, STF####
- **Management**: Reserved IDs, allocation history

## 🚀 Development

### Adding New Tools
1. Create new tool blueprint in `tools/` directory
2. Create corresponding template in `templates/tools/`
3. Register blueprint in `app.py`
4. Add tool metadata to `tools/__init__.py`

### Customization
- Modify `config.py` for environment-specific settings
- Update `static/css/custom.css` for styling
- Extend `utils/` for additional functionality

## 🔒 Security

- File upload validation and sanitization
- CSRF protection enabled
- Secure file storage with automatic cleanup
- Input validation and sanitization
- Session security configurations

## 📊 Monitoring & Analytics

- Usage tracking and statistics
- Error monitoring and logging
- Performance metrics
- User activity patterns

## 🌐 Deployment

### Development
```bash
FLASK_ENV=development python app.py
```

### Production
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Using Docker
docker build -t hr-toolkit .
docker run -p 8000:8000 hr-toolkit
```

### Environment Variables
```bash
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/database.db
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=16777216
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 Changelog

### v1.0.0 (2025-11-04)
- Initial release with 6 core tools
- Modern responsive UI with dark mode
- Search and filtering capabilities
- Analytics dashboard
- Security enhancements
- File upload and processing
- Mobile responsive design

## 📞 Support

For support or questions:
- Email: hr-ops@247-inc.com
- Extension: 010111628
- Response time: Usually within 24 hours

## 📄 License

This project is proprietary software developed for internal use by [24]7.ai HR Operations.

---

**Developed by**: HR Operations Team (010111628)
**For**: Internal operational use only
**© 2025 [24]7.ai. All Rights Reserved.**

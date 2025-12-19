# AutoLight Analyser

A comprehensive Django-based full-stack application for analyzing CAD files, managing lighting fixtures, and generating detailed lighting reports for architectural projects.

## 🌟 Features

### Core Functionality
- **CAD File Upload & Processing**: Upload and parse `.dwg` and `.dxf` files
- **Lighting Analysis**: Automatic detection and analysis of lighting fixtures from CAD files
- **Room Mapping**: Intelligent room detection and fixture-to-room mapping
- **Report Generation**: Generate professional PDF and CSV reports
- **Interactive Dashboard**: Real-time analytics with Chart.js visualizations
- **Fixture Catalog**: Comprehensive database of lighting fixtures with specifications
- **Cost Calculations**: Automatic project cost estimation and quotations
- **User Roles**: Role-based access control (Admin, Architect, Vendor)

### Frontend Features
- ✅ Responsive design with Bootstrap 5
- ✅ Dark/Light theme toggle
- ✅ Interactive charts (Bar, Pie, Line) using Chart.js
- ✅ Real-time price updates when selecting alternatives
- ✅ Client-side PDF export using html2pdf.js
- ✅ Mobile-friendly layouts
- ✅ Print-ready quotation formats

### Backend Features
- ✅ Django 6.0 framework
- ✅ SQLite database (easily swappable to PostgreSQL/MySQL)
- ✅ CAD file parsing with `ezdxf` library
- ✅ PDF generation with ReportLab
- ✅ CSV export functionality
- ✅ User authentication and authorization
- ✅ Django admin interface for data management
- ✅ Fixture recommendation system
- ✅ Lux calculations and lighting adequacy checks

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd /home/user/webapp
   ```

2. **Install dependencies**:
   ```bash
   pip3 install django ezdxf reportlab celery redis pillow
   ```

3. **Run migrations**:
   ```bash
   python3 manage.py migrate
   ```

4. **Load sample data**:
   ```bash
   python3 manage.py load_sample_data
   ```

5. **Start the development server**:
   ```bash
   python3 manage.py runserver 0.0.0.0:8000
   ```

6. **Access the application**:
   - Main Application: `http://localhost:8000/`
   - Admin Interface: `http://localhost:8000/admin/`

### Default Credentials

**Demo User:**
- Username: `demo`
- Password: `demo1234`
- Role: Architect

**Admin User:**
- Username: `admin`
- Password: `admin123`
- Role: Superuser

## 📁 Project Structure

```
webapp/
├── autolight_project/       # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── lighting/                # Main application
│   ├── management/          # Custom management commands
│   │   └── commands/
│   │       └── load_sample_data.py
│   ├── migrations/          # Database migrations
│   ├── templates/           # HTML templates
│   │   └── lighting/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── upload.html
│   │       ├── results.html
│   │       ├── login.html
│   │       ├── register.html
│   │       └── catalog.html
│   ├── admin.py            # Admin interface configuration
│   ├── forms.py            # Form definitions
│   ├── models.py           # Database models
│   ├── urls.py             # URL routing
│   ├── utils.py            # Utility functions
│   └── views.py            # View controllers
├── media/                   # User-uploaded files
│   ├── cad_files/
│   ├── fixtures/
│   └── reports/
├── static/                  # Static assets
│   ├── css/
│   └── js/
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
└── README.md               # This file
```

## 🗄️ Database Models

### LightingCatalog
Stores information about available lighting fixtures:
- Symbol name (CAD block name)
- Brand and model number
- Technical specifications (lumens, wattage, beam angle, color temperature)
- Unit cost
- Image

### CADFile
Tracks uploaded CAD files:
- User association
- Project name and filename
- Processing status
- Upload and processing timestamps

### Room
Represents rooms detected from CAD files:
- Room name and dimensions (area, height)
- Required and current lux levels
- Association with CAD file

### Fixture
Links lighting fixtures to rooms:
- Lighting catalog reference
- Quantity
- Coordinates from CAD file
- Calculated properties (total lumens, cost)

### Report
Tracks generated reports:
- CAD file reference
- Report type (PDF/CSV)
- File path
- Generation timestamp

## 🎨 Frontend Components

### 1. Dashboard (`dashboard.html`)
- **Summary Cards**: Total projects, fixtures, average lux
- **Charts**:
  - Bar Chart: Fixtures per room
  - Pie Chart: Fixture types distribution
  - Line Chart: Lux trends across projects
- **Recent Projects Table**: Quick access to project reports

### 2. Upload Page (`upload.html`)
- File upload form with validation
- Optional symbol legend mapping (JSON)
- Progress indicator
- Helpful usage instructions

### 3. Results Page (`results.html`)
- Project information summary
- Room-by-room analysis
- Detailed fixtures table with:
  - Detected symbols
  - Selected fixtures
  - Specifications and pricing
  - Alternative recommendations
- Interactive alternative selection
- Real-time cost updates
- Export options (PDF, CSV)

### 4. Base Template (`base.html`)
- Responsive navigation
- Dark/light theme toggle
- User authentication status
- Bootstrap 5 integration
- Chart.js and html2pdf.js libraries

## 🔧 Key Utility Functions

### CAD Processing
- `parse_cad(file_path)`: Parse DWG/DXF files and extract blocks
- `calculate_polyline_area(points)`: Calculate room areas from polylines
- `map_symbols_to_catalog(symbols, legend)`: Map CAD symbols to catalog entries
- `process_cad_file(cad_file, legend)`: Complete CAD file processing pipeline

### Lighting Calculations
- `calculate_required_fixtures(room_area, lumens_per_fixture, required_lux)`: Calculate fixture requirements
- `calculate_room_lux(fixtures_list, room_area)`: Calculate current illuminance

### Report Generation
- `generate_pdf_report(cad_file)`: Create comprehensive PDF report
- `generate_csv_report(cad_file)`: Export data to CSV format

## 🔐 Authentication & Roles

### User Groups
1. **Admin**: Full system access, user management
2. **Architect**: Create projects, upload CAD files, generate reports
3. **Vendor**: View catalog, access reports (limited)

### Protected Views
All main views require authentication (`@login_required` decorator)

## 📊 Sample Lighting Catalog

The system comes pre-loaded with 10 sample fixtures:
- LED Panels (600x600, 300x1200)
- Downlights (8W, 12W)
- Track Lights (20W)
- Linear LEDs (40W)
- High Bays (150W)
- Floodlights (50W)
- Bulkheads (18W)
- LED Strips (14W)

## 🧪 Testing the Application

### Test Workflow

1. **Login**:
   ```
   URL: http://localhost:8000/login/
   Credentials: demo / demo1234
   ```

2. **Upload a CAD File**:
   - Navigate to Upload page
   - Provide a project name
   - Select a `.dxf` or `.dwg` file
   - Optionally provide a symbol legend

3. **View Results**:
   - After processing, view the analysis results
   - Explore alternative fixture recommendations
   - Update selections to recalculate costs

4. **Generate Reports**:
   - Click "Download as PDF" for client-ready quotation
   - Click "Full Report (PDF)" for detailed analysis
   - Click "Download as CSV" for data export

5. **Dashboard Analytics**:
   - View summary statistics
   - Explore interactive charts
   - Access recent projects

## 🎯 Future Enhancements

### Optional Features (Ready for Implementation)

1. **Celery Integration**:
   - Async processing for large CAD files
   - Background report generation
   - Redis broker already configured in settings

2. **Advanced Features**:
   - 3D visualization of room layouts
   - Energy consumption calculations
   - Lighting simulation and rendering
   - Multi-project comparison
   - Export to BIM formats

3. **API Development**:
   - REST API with Django REST Framework
   - Mobile app integration
   - Third-party integrations

## 🛠️ Development

### Running Tests
```bash
python3 manage.py test lighting
```

### Creating Migrations
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### Collecting Static Files
```bash
python3 manage.py collectstatic
```

### Creating Superuser
```bash
python3 manage.py createsuperuser
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Database Errors**: Run migrations
   ```bash
   python3 manage.py migrate
   ```

3. **Static Files Not Loading**: Collect static files
   ```bash
   python3 manage.py collectstatic
   ```

4. **CAD Parsing Errors**: Ensure CAD file is valid DWG/DXF format

## 📝 License

This project is for demonstration purposes.

## 👥 Credits

Developed as a comprehensive Django full-stack application demonstrating:
- CAD file processing
- Lighting analysis and calculations
- Report generation
- Interactive dashboards
- Role-based access control
- Responsive web design

---

**Note**: This is a development version. For production deployment:
- Set `DEBUG = False` in settings.py
- Configure proper SECRET_KEY
- Use PostgreSQL or MySQL database
- Set up proper ALLOWED_HOSTS
- Configure static file serving (WhiteNoise, nginx)
- Enable HTTPS
- Set up Celery workers for async processing

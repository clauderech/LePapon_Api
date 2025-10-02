# LePapon System - AI Coding Instructions

## Architecture Overview

LePapon is a multi-component restaurant management system built with Python and Flet (Python's GUI framework). The system consists of:

- **app_admin**: Administrative interface for financial control, inventory, and reporting
- **PDV_API**: Point-of-sale terminal with client management and order processing
- **LePapon_Cozinha**: Kitchen display system for order management
- **Baixar_Pedidos_DigOcean**: Order download service from external APIs
- **Scan_Converter_IA**: PDF/document processing with AI integration
- **Produtos_Manager**: Product catalog management

## Key Patterns and Conventions

### API Client Pattern
All API interactions follow a consistent pattern using dedicated API classes:
```python
class VendasAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
    
    def get_all(self):
        return requests.get(f"{self.base_url}/api/vendas").json()
    
    def create(self, data):
        return requests.post(f"{self.base_url}/api/vendas", json=data).json()
```

### Flet View Architecture
All main applications use Flet with a navigation-based routing system:
- Views are functions that return Flet components
- Routes are defined in a `views` dictionary mapping paths to view functions
- Each app has a `main(page: ft.Page)` function with route change handlers

### Base Classes and Utilities
- `BaseView` class in `app_admin/utils/base_view.py` provides common functionality for data filtering and client management
- `common_utils.py` contains shared utilities like `BASE_URL`, date formatting, and parsing functions
- All API clients should inherit base URL from `common_utils.BASE_URL`

## Development Workflows

### Adding New Features
1. Create API client in `models/` directory following the established pattern
2. Create view function in `views/` directory
3. Add route mapping in main.py's `views` dictionary
4. Update navigation bar destinations if needed

### Database Integration
- Direct MySQL connections used in scripts (see `app_admin/scripts/inserir_controle_semanal.py`)
- Database config typically includes: user, password, host, database name
- Use parameterized queries for security

### File Structure Conventions
- `models/`: API clients and data models
- `views/`: UI components and view functions  
- `utils/`: Shared utilities and base classes
- `scripts/`: Automation and data processing scripts
- `Crediario/`: Customer credit file storage (organized by customer name)

## Integration Points

### External API Communication
- Base API URL: `http://lepapon.api:3000`
- All API endpoints follow REST conventions (`/api/{resource}`)
- Standard CRUD operations: GET, POST, PUT, DELETE

### Cross-Component Communication
- Components communicate through shared API endpoints
- Kitchen system (`LePapon_Cozinha`) displays orders from PDV system
- Admin system monitors all financial transactions

### Dependencies
- **Flet**: UI framework (all main applications)
- **requests**: HTTP client for API communication
- **pandas**: Data processing and analysis
- **mysql-connector**: Direct database access in scripts

## AI-Specific Considerations

### PDF Processing (Scan_Converter_IA)
- Uses Gemini AI for PDF text extraction
- Processes supplier invoices and converts to JSON
- Automatic date conversion and API integration

### File Organization
- Customer credit files stored with normalized names (spaces replaced with underscores)
- JSON responses cached for AI processing workflows
- Separate `.env` files for different components

## Common Pitfalls
- Always strip trailing slashes from base URLs in API clients
- Use `parse_float()` utility for handling Brazilian decimal format (comma as decimal separator)
- Views must return valid Flet components or None
- API responses should be checked for list vs single object returns
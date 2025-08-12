# Security Access Control System

## Overview

This is a Flask-based security access control system that provides QR code-based authentication and user management capabilities. The application serves as a security checkpoint system where users can scan QR codes for access verification, and administrators can manage users and monitor activity through a comprehensive dashboard.

The system is designed for physical access control scenarios such as building entrances, event venues, or secure facilities, providing real-time access verification and detailed activity logging.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework Architecture
- **Flask Application**: Core web framework with SQLAlchemy for database operations
- **Template Engine**: Jinja2 templating with Bootstrap 5 for responsive UI
- **Static Assets**: CSS and JavaScript files for enhanced user experience
- **WSGI Configuration**: ProxyFix middleware for proper URL generation behind proxies

### Authentication and Authorization
- **Replit OAuth Integration**: Primary authentication mechanism using Flask-Dance
- **Flask-Login**: Session management and user state tracking
- **User Model**: SQLAlchemy-based user storage with OAuth token management
- **Admin Access Control**: Role-based access to administrative functions

### Data Storage Strategy
- **Dual Storage Approach**: 
  - SQLAlchemy models for user authentication (required for Replit Auth)
  - In-memory data store (`SecurityDataStore`) for security access data
- **Database Flexibility**: Configurable database URI supporting SQLite (default) and PostgreSQL
- **Connection Pooling**: Pre-ping and connection recycling for reliability

### Frontend Architecture
- **Responsive Design**: Bootstrap 5 framework for mobile-first UI
- **Component-Based Templates**: Modular template inheritance structure
- **Interactive Elements**: JavaScript for enhanced UX including auto-dismiss alerts and form validation
- **Accessibility**: Font Awesome icons and semantic HTML structure

### Security Access Control Logic
- **QR Code Processing**: Input validation and uppercase normalization
- **Access Verification**: Real-time lookup against user database
- **Activity Logging**: Comprehensive tracking of all access attempts
- **Status Management**: User status controls (allowed/banned) with check-in/out tracking

### Administrative Interface
- **Dashboard Analytics**: Real-time statistics and user management
- **User Management**: CRUD operations for user accounts
- **Activity Reports**: Filtered reporting with CSV export capabilities
- **Bulk Operations**: Support for batch user management tasks

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-Login**: User session management
- **Flask-Dance**: OAuth provider integration for Replit Auth

### UI and Frontend Libraries
- **Bootstrap 5**: CSS framework via CDN
- **Font Awesome 6**: Icon library via CDN
- **Custom CSS/JS**: Enhanced styling and interactive functionality

### Database Support
- **SQLite**: Default database for development and simple deployments
- **PostgreSQL**: Production database option via DATABASE_URL environment variable
- **SQLAlchemy**: Database abstraction layer with connection pooling

### Authentication Services
- **Replit OAuth**: Primary authentication provider
- **JWT**: Token handling for secure authentication flows

### Environment Configuration
- **Environment Variables**: 
  - `SESSION_SECRET`: Flask session security
  - `DATABASE_URL`: Database connection string
- **Logging**: Configurable logging with debug support for development

### Development and Deployment
- **Werkzeug**: WSGI utilities and development server
- **ProxyFix**: Middleware for proper HTTPS URL generation
- **Debug Mode**: Development-friendly error handling and auto-reload
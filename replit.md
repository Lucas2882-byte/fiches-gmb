# Replit Configuration

## Overview

This is a Streamlit-based web application for managing "Fiches GMB" (GMB Forms/Sheets). The application appears to be a business management tool that handles form creation, data storage, and potentially email communications. Built with Python and Streamlit, it provides a web interface for users to interact with business data through forms and visualizations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework providing reactive UI components
- **Layout**: Wide page layout configuration for better data presentation
- **Styling**: Custom color palette with 30 predefined colors for consistent theming across the application

### Backend Architecture
- **Database**: SQLite for local data persistence - lightweight, serverless database solution
- **Web Framework**: Streamlit handles both frontend rendering and backend logic in a single Python application
- **File Processing**: Built-in support for ZIP file creation and manipulation using BytesIO for in-memory operations

### Data Storage Solutions
- **Primary Database**: SQLite3 for structured data storage
- **File Storage**: Local file system for document and ZIP archive management
- **Session Management**: Streamlit's built-in session state for user data persistence

### Authentication and Security
- **Password Hashing**: SHA-256 hashing algorithm for secure password storage
- **Encoding**: Base64 encoding for data serialization and transmission

### Communication Systems
- **Email Integration**: SMTP client for automated email notifications and communications
- **Text Processing**: Unicode normalization and regex pattern matching for data validation and cleaning

## External Dependencies

### Core Framework Dependencies
- **Streamlit**: Web application framework for rapid prototyping and deployment
- **Pandas**: Data manipulation and analysis library
- **Requests**: HTTP library for external API communications

### Built-in Python Libraries
- **SQLite3**: Database connectivity and operations
- **Base64**: Data encoding and decoding utilities
- **Datetime**: Date and time manipulation for scheduling and timestamps
- **Zipfile**: Archive creation and extraction capabilities
- **Re/Unicodedata**: Text processing and validation
- **SMTPLIB**: Email sending functionality
- **Hashlib**: Cryptographic hashing for security features
- **OS**: Operating system interface for file operations
- **Time**: Time-based operations and delays
- **IO**: Input/output operations including BytesIO for memory streams

### Potential External Services
- **Email Providers**: SMTP servers for email delivery (Gmail, Outlook, custom SMTP)
- **File Storage**: Local file system with potential for cloud storage integration
- **Web APIs**: HTTP requests capability suggests integration with external REST APIs or web services
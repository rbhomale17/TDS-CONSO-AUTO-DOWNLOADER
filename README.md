# TDS-CONSO-AUTO-DOWNLOADER

A Python-based automation tool for downloading TDS (Tax Deducted at Source) Consolidated files from TRACES (TDS Reconciliation Analysis and Correction Enabling System) portal.

## Features

- Automated login to TRACES portal
- Manual CAPTCHA handling for secure authentication
- Bulk download of NSDL Consolidated files
- Custom file naming with TAN number
- Automatic extraction of downloaded zip files
- Organized file management system

## Prerequisites

- Python 3.6 or higher
- Chrome browser installed
- Chrome WebDriver compatible with your Chrome version
- Tesseract OCR (for potential future CAPTCHA automation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/TDS-CONSO-AUTO-DOWNLOADER.git
cd TDS-CONSO-AUTO-DOWNLOADER
```

2. Install required dependencies:
```bash
pip install -r req.txt
```

## Configuration

Before running the scripts, you need to configure your credentials:

1. Open either `singal_top_CONSO_scrape.py` or `multi_scrapper_with_custom_naming.py`
2. Replace the following placeholders with your actual credentials:
```python
username = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
tan = "YOUR_TAN_NUMBER"
```

## Usage

### Single TDS File Download

To download a single TDS consolidated file:

```bash
python singal_top_CONSO_scrape.py
```

### Multiple TDS Files Download with Custom Naming

To download multiple TDS consolidated files with custom naming:

```bash
python multi_scrapper_with_custom_naming.py
```

## Directory Structure

The scripts will create the following directory structure:

```
project_root/
├── downloads/
│   └── {TAN}_CONSO/      # Downloaded zip files
├── extracted/
│   └── {TAN}/            # Temporary extraction directory
├── tds_files/
│   └── {TAN}_CONSO/      # Final .tds files location
```

## Features Comparison

1. `singal_top_CONSO_scrape.py`:
   - Basic single file download
   - Simple implementation
   - Suitable for one-time downloads

2. `multi_scrapper_with_custom_naming.py`:
   - Bulk download capability
   - Custom file naming with TAN
   - Automatic file organization
   - ZIP extraction with password handling
   - Pagination support for multiple pages

## Important Notes

1. CAPTCHA handling is manual - you'll need to input the CAPTCHA text when prompted
2. Keep your credentials secure and never share them
3. The scripts include automatic cleanup of temporary files and directories
4. Downloads are organized by TAN number for better management

## Error Handling

The scripts include comprehensive error handling for:
- Login failures
- Network timeouts
- Invalid credentials
- File download issues
- ZIP extraction errors

## Contributing

Feel free to fork this repository and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

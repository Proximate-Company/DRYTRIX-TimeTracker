# PDF Generation Troubleshooting Guide

## Common Error: `gobject-2.0-0` Library Missing

### Error Message
```
Error generating PDF: cannot load library 'gobject-2.0-0': gobject-2.0-0: cannot open shared object file: No such file or directory. Additionally, ctypes.util.find_library() did not manage to locate a library called 'gobject-2.0-0'
```

### What This Means
WeasyPrint requires several system libraries for rendering HTML/CSS to PDF. The `gobject-2.0-0` library is part of the GLib/GObject system that WeasyPrint uses for rendering.

### Solutions

#### Option 1: Fix System Dependencies (Recommended)
Update your Dockerfile to include the required system libraries:

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    # WeasyPrint dependencies
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libpangocairo-1.0-0 \
    libffi-dev \
    shared-mime-info \
    # Additional fonts and rendering support
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
```

Then rebuild your Docker container:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

#### Option 2: Use ReportLab Fallback (Already Configured)
The system automatically falls back to ReportLab when WeasyPrint fails. ReportLab generates basic but functional PDFs without external dependencies.

**Pros:**
- No system dependencies required
- Always works
- Faster generation

**Cons:**
- Less styling control
- No CSS support
- Basic layout only

#### Option 3: Alternative PDF Libraries
Consider these alternatives if both WeasyPrint and ReportLab fail:

```bash
# Install alternative PDF libraries
pip install pdfkit  # Requires wkhtmltopdf
pip install xhtml2pdf  # Pure Python, limited features
```

### Testing PDF Generation

Run the test script to diagnose issues:

```bash
# Inside the container
python /app/docker/test-pdf-generation.py

# Or from host
docker exec -it your-container-name python /app/docker/test-pdf-generation.py
```

### Expected Output

#### Successful WeasyPrint Test:
```
=== PDF Generation Test ===
Checking system libraries:
✓ gobject-2.0-0: /usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0
✓ pango-1.0-0: /usr/lib/x86_64-linux-gnu/libpango-1.0.so.0
✓ cairo: /usr/lib/x86_64-linux-gnu/libcairo.so.2
✓ gdk_pixbuf-2.0: /usr/lib/x86_64-linux-gnu/libgdk_pixbuf-2.0.so.0

=== Python Libraries ===
✓ WeasyPrint is available

=== Summary ===
✓ WeasyPrint is working - High-quality PDFs available
```

#### WeasyPrint Failed, ReportLab Available:
```
=== Summary ===
⚠ WeasyPrint failed but ReportLab is available - Basic PDFs available

=== Recommendations ===
1. Install system dependencies: libgdk-pixbuf2.0-0, libpango-1.0-0, libcairo2
2. Rebuild Docker container with updated Dockerfile
3. Or use ReportLab fallback (already configured)
```

### System Library Details

#### Required Libraries:
- **libgdk-pixbuf2.0-0**: Image loading and manipulation
- **libpango-1.0-0**: Text layout and rendering
- **libcairo2**: 2D graphics rendering
- **libpangocairo-1.0-0**: Pango-Cairo integration
- **libffi-dev**: Foreign function interface
- **shared-mime-info**: MIME type detection

#### Font Support:
- **fonts-liberation**: Open-source font alternatives
- **fonts-dejavu-core**: Additional font support

### Docker Container Issues

#### Common Problems:
1. **Base Image**: `python:3.11-slim` is minimal and may lack libraries
2. **Architecture**: ARM vs x86_64 can have different library names
3. **Package Names**: Package names may vary between distributions

#### Solutions:
1. **Use Debian-based image**: `python:3.11-slim` is Debian-based
2. **Install build tools**: Add `build-essential` if compiling from source
3. **Check package names**: Verify package names with `apt-cache search`

### Performance Considerations

#### WeasyPrint:
- **Memory**: Higher memory usage during generation
- **Speed**: Slower for complex layouts
- **Quality**: Professional-grade output

#### ReportLab:
- **Memory**: Lower memory usage
- **Speed**: Faster generation
- **Quality**: Basic but functional

### Troubleshooting Steps

1. **Check Current Status**:
   ```bash
   docker exec -it your-container-name python /app/docker/test-pdf-generation.py
   ```

2. **Verify System Libraries**:
   ```bash
   docker exec -it your-container-name ldconfig -p | grep -E "(gobject|pango|cairo)"
   ```

3. **Check Package Installation**:
   ```bash
   docker exec -it your-container-name dpkg -l | grep -E "(libgdk|libpango|libcairo)"
   ```

4. **Rebuild Container**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

5. **Test PDF Generation**:
   - Try generating a PDF from an invoice
   - Check for fallback to ReportLab
   - Verify PDF output quality

### Fallback Configuration

The system automatically detects WeasyPrint failures and switches to ReportLab:

```python
try:
    from app.utils.pdf_generator import InvoicePDFGenerator
    # Use WeasyPrint
except Exception as e:
    try:
        from app.utils.pdf_generator_fallback import InvoicePDFGeneratorFallback
        # Use ReportLab fallback
    except Exception as fallback_error:
        # Both failed
```

### Support and Maintenance

#### Regular Tasks:
- Monitor PDF generation logs
- Test both generators periodically
- Update system dependencies as needed

#### When to Rebuild:
- After system updates
- When adding new PDF features
- If performance degrades

### Conclusion

The PDF generation system is designed with fallbacks to ensure reliability:

1. **Primary**: WeasyPrint for high-quality PDFs
2. **Fallback**: ReportLab for basic PDFs
3. **Automatic**: Seamless switching between generators

Most users will get working PDFs immediately, with the option to upgrade to high-quality output by fixing system dependencies.

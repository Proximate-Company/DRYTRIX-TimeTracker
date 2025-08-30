# Company Logo Upload System

## Overview

The TimeTracker application now includes a modern, user-friendly company logo upload system that replaces the previous file path-based approach. This system allows administrators to upload company logos directly through the web interface, making it much easier to customize the application's branding.

## Features

### 🎯 **Easy Logo Management**
- **Direct Upload**: Upload logos through the web interface
- **Multiple Formats**: Support for PNG, JPG, JPEG, GIF, SVG, and WEBP
- **File Validation**: Automatic file type and size validation
- **Preview**: See how your logo will look before uploading
- **Automatic Replacement**: Old logos are automatically removed when new ones are uploaded

### 🖼️ **Supported File Types**
- **PNG** - Portable Network Graphics
- **JPG/JPEG** - Joint Photographic Experts Group
- **GIF** - Graphics Interchange Format
- **SVG** - Scalable Vector Graphics
- **WEBP** - Web Picture format

### 📏 **File Requirements**
- **Maximum Size**: 5MB
- **Recommended Dimensions**: 200x200 pixels or larger
- **Format**: Any of the supported image formats above

## Installation & Setup

### 1. **Run the Migration Script**

First, run the logo upload system migration:

```bash
cd docker
python migrate-logo-upload.py
```

This script will:
- Update your database schema from `company_logo_path` to `company_logo_filename`
- Create the necessary upload directories
- Preserve existing logo paths (if they exist and are accessible)

### 2. **Restart Your Application**

After running the migration, restart your TimeTracker application to ensure all changes take effect.

### 3. **Access the Logo Upload Interface**

1. Log in as an administrator
2. Go to **Admin → Settings**
3. Scroll down to the **Company Branding** section
4. Use the new logo upload interface

## Usage Guide

### **Uploading a New Logo**

1. **Navigate to Settings**
   - Go to Admin → Settings
   - Scroll to the Company Branding section

2. **Choose Your Logo File**
   - Click "Choose File" or drag and drop your logo
   - Select a supported image format (PNG, JPG, SVG, etc.)
   - Ensure the file is under 5MB

3. **Preview Your Logo**
   - The system will show a preview of your logo
   - Verify it looks correct before uploading

4. **Upload the Logo**
   - Click "Upload Logo"
   - Wait for the upload to complete
   - The page will refresh to show your new logo

### **Managing Existing Logos**

#### **View Current Logo**
- Your current logo is displayed above the upload controls
- Shows the actual logo image, not just a file path

#### **Remove Current Logo**
- Click the "Remove Logo" button below your current logo
- Confirm the removal when prompted
- The system will return to the default logo

#### **Replace Logo**
- Simply upload a new logo file
- The old logo is automatically removed
- No manual cleanup required

## Technical Details

### **File Storage**
- **Location**: `app/static/uploads/logos/`
- **Naming**: Files are automatically renamed with unique identifiers
- **Security**: Only image files are allowed
- **Cleanup**: Old files are automatically removed

### **Database Changes**
- **Old Field**: `company_logo_path` (VARCHAR(500))
- **New Field**: `company_logo_filename` (VARCHAR(255))
- **Migration**: Automatic conversion from paths to filenames

### **URL Structure**
- **Logo URLs**: `/uploads/logos/filename.ext`
- **Fallback**: Default logo if no custom logo is uploaded
- **Caching**: Logos are served as static files for performance

## Integration Points

### **Where Your Logo Appears**

1. **Application Header**
   - Navigation bar logo
   - Favicon (browser tab icon)

2. **Login Page**
   - Welcome screen logo
   - Authentication branding

3. **Dashboard**
   - Welcome message area
   - Application branding

4. **PDF Invoices**
   - Company header
   - Professional branding

5. **Help & About Pages**
   - Company information
   - Brand consistency

### **Template Updates**

The following templates automatically use your uploaded logo:
- `base.html` - Main application template
- `auth/login.html` - Login page
- `main/dashboard.html` - Dashboard
- `main/help.html` - Help page
- `main/about.html` - About page
- PDF invoice generation

## Troubleshooting

### **Common Issues**

#### **Logo Not Appearing**
- Check if the logo file was uploaded successfully
- Verify the file format is supported
- Ensure the file size is under 5MB
- Check browser console for JavaScript errors

#### **Upload Fails**
- Verify you have administrator privileges
- Check file format and size requirements
- Ensure the uploads directory has write permissions
- Check application logs for server-side errors

#### **Migration Issues**
- Ensure the company branding migration ran first
- Check database connection and permissions
- Verify the settings table exists
- Run the migration script with proper database credentials

### **File Permission Issues**

If you encounter permission problems:

```bash
# Set proper permissions on uploads directory
chmod -R 755 app/static/uploads/
chown -R www-data:www-data app/static/uploads/  # Adjust user/group as needed
```

### **Database Connection Issues**

Ensure your database connection is working:

```bash
# Test database connection
python -c "from app import create_app; app = create_app(); print('Database connection OK')"
```

## Security Considerations

### **File Validation**
- **Type Checking**: Only image files are allowed
- **Size Limits**: Maximum 5MB file size
- **Extension Validation**: Strict file extension checking
- **Content Verification**: File content is validated

### **Access Control**
- **Admin Only**: Logo upload requires administrator privileges
- **Authenticated Users**: Logo viewing requires user authentication
- **Session Management**: Proper session handling for uploads

### **File Storage**
- **Isolated Directory**: Logos stored in dedicated uploads folder
- **Unique Naming**: Files renamed to prevent conflicts
- **Automatic Cleanup**: Old files removed when replaced

## Performance Optimization

### **Image Optimization**
- **Format Selection**: Choose appropriate formats for your use case
- **Size Optimization**: Compress images before uploading
- **SVG Benefits**: Use SVG for logos that need to scale

### **Caching**
- **Static File Serving**: Logos served as static files
- **Browser Caching**: Proper cache headers for performance
- **CDN Ready**: Structure supports CDN integration

## Future Enhancements

### **Planned Features**
- **Multiple Logo Support**: Different logos for different contexts
- **Logo Cropping**: Built-in image editing tools
- **Logo Templates**: Pre-designed logo templates
- **Bulk Logo Management**: Multiple logo upload support

### **Integration Opportunities**
- **Logo API**: REST API for logo management
- **Third-party Services**: Integration with design tools
- **Automated Branding**: AI-powered logo suggestions
- **Logo Analytics**: Usage tracking and insights

## Support & Maintenance

### **Regular Maintenance**
- **File Cleanup**: Remove unused logo files
- **Storage Monitoring**: Track upload directory size
- **Backup Strategy**: Include logos in regular backups
- **Performance Monitoring**: Monitor logo loading times

### **Getting Help**
- **Documentation**: This README and inline code comments
- **Error Logs**: Check application logs for detailed error information
- **Community**: TimeTracker community forums and discussions
- **Issues**: Report bugs through the project's issue tracker

## Conclusion

The new logo upload system provides a much more user-friendly and professional way to manage company branding in TimeTracker. By eliminating the need for manual file path configuration, it makes the application more accessible to non-technical users while maintaining all the security and performance benefits of the previous system.

The system is designed to be:
- **Easy to Use**: Simple upload interface with preview
- **Secure**: Proper validation and access control
- **Reliable**: Automatic file management and cleanup
- **Scalable**: Ready for future enhancements and integrations

For questions or support, please refer to the troubleshooting section above or consult the TimeTracker documentation.

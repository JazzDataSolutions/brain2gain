# Email Templates System - Brain2Gain

## Overview

The Brain2Gain platform includes a comprehensive email template system built with MJML for creating responsive, professional email communications. This system provides:

- **MJML Template Compilation**: Professional email templates that render perfectly across all email clients
- **Dynamic Data Population**: Jinja2-powered template variables for personalized content
- **API-based Management**: Admin endpoints for template preview, testing, and management
- **Integration with Notification Service**: Seamless email sending with template support
- **Fallback Support**: Graceful degradation when MJML CLI is not available

## Available Templates

### Core Transactional Templates

1. **Order Confirmation** (`order_confirmation`)
   - Sent when customer places an order
   - Includes order details, payment info, shipping address
   - Variables: `order_id`, `customer_name`, `order_items`, `total_amount`, etc.

2. **Order Shipped** (`order_shipped`)
   - Sent when order is dispatched
   - Includes tracking information and delivery estimates
   - Variables: `tracking_number`, `carrier_name`, `estimated_delivery`, etc.

3. **Order Delivered** (`order_delivered`)
   - Sent when order is successfully delivered
   - Includes delivery confirmation and review request
   - Variables: `delivered_date`, `review_url`, `reorder_url`, etc.

4. **Password Reset** (`reset_password`)
   - Sent for password reset requests
   - Includes secure reset link with expiration
   - Variables: `username`, `link`, `valid_hours`

5. **New Account** (`new_account`)
   - Sent for new user registrations
   - Includes account details and welcome message
   - Variables: `username`, `password`, `link`

## API Endpoints

All email template endpoints require admin authentication and are prefixed with `/api/v1/email-templates/`.

### Template Management

- `GET /` - List all available templates
- `GET /{template_name}/preview` - Preview template with sample data
- `GET /{template_name}/validate` - Validate template structure
- `GET /sample-data/{template_name}` - Get sample data structure
- `GET /health` - Service health check

### Template Testing

- `POST /{template_name}/compile` - Compile template with custom data
- `POST /{template_name}/test-send` - Send test email to specified address
- `DELETE /cache` - Clear template compilation cache

### Example API Usage

```bash
# Health check
curl http://localhost:8000/api/v1/email-templates/health

# Preview order confirmation template
curl http://localhost:8000/api/v1/email-templates/order_confirmation/preview

# Send test email
curl -X POST http://localhost:8000/api/v1/email-templates/order_confirmation/test-send \
  -H "Authorization: Bearer <admin_token>" \
  -G -d "recipient_email=test@example.com"
```

## Integration with Notification Service

The email templates are automatically integrated with the NotificationService:

```python
from app.services.notification_service import NotificationService, NotificationType, NotificationTemplate

# Send order confirmation email
await notification_service.send_notification(
    recipient="customer@example.com",
    notification_type=NotificationType.EMAIL,
    template=NotificationTemplate.ORDER_CONFIRMATION,
    data={
        "customer_name": "Juan Pérez",
        "order_id": "BG-2025-001234",
        "total_amount": "89.99",
        # ... other template variables
    }
)
```

## Template Development

### File Structure

```
backend/app/email-templates/
├── src/                     # MJML source templates
│   ├── order_confirmation.mjml
│   ├── order_shipped.mjml
│   ├── order_delivered.mjml
│   ├── reset_password.mjml
│   └── new_account.mjml
└── compiled/               # Compiled HTML cache
    └── *.html
```

### Template Variables

Templates use Jinja2 syntax for variable substitution:

```mjml
<mj-text>Hello {{ customer_name }},</mj-text>
<mj-text>Your order #{{ order_id }} has been confirmed.</mj-text>

{% for item in order_items %}
<mj-table>
  <tr>
    <td>{{ item.product_name }}</td>
    <td>${{ item.total_price }}</td>
  </tr>
</mj-table>
{% endfor %}
```

### Adding New Templates

1. Create MJML file in `app/email-templates/src/`
2. Add template mapping in `NotificationService._get_mjml_template_name()`
3. Add sample data in `EmailTemplateService._get_sample_data()`
4. Add template enum in `NotificationTemplate` if needed

### MJML Installation (Optional)

For best results, install MJML CLI:

```bash
npm install -g mjml
```

Set `MJML_CLI_ENABLED=true` in environment variables.

## Configuration

### Environment Variables

```env
# Email service provider
EMAIL_SERVICE=smtp                    # smtp, sendgrid, mailgun, ses
SENDGRID_API_KEY=your_sendgrid_key   # If using SendGrid
MAILGUN_API_KEY=your_mailgun_key     # If using Mailgun
MAILGUN_DOMAIN=your_domain           # If using Mailgun

# SMTP configuration (default)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAILS_FROM_EMAIL=noreply@brain2gain.com
EMAILS_FROM_NAME=Brain2Gain

# Template configuration
EMAIL_TEMPLATE_CACHE_TTL=3600        # Cache TTL in seconds
EMAIL_TEMPLATE_FALLBACK_ENABLED=true # Enable fallback conversion
MJML_CLI_ENABLED=false               # Set true if MJML CLI installed
```

## Monitoring and Debugging

### Development Mode

In local development, compiled emails are saved as HTML files for preview:

```bash
# Check logs for preview file locations
tail -f logs/app.log | grep "Email preview saved"
```

### Testing Templates

Use the built-in testing endpoints to validate templates:

```python
# Test template compilation
result = await email_template_service.validate_template("order_confirmation")
print(result)

# Generate preview
html = await email_template_service.get_template_preview("order_confirmation")
```

### Performance Monitoring

- Template compilation is cached for performance
- Cache hit/miss metrics available in logs
- Template file modification timestamps tracked

## Security Considerations

- All template endpoints require admin authentication
- Template data is sanitized through Jinja2 autoescape
- Email content is validated before sending
- Test emails include metadata for audit trail

## Troubleshooting

### Common Issues

1. **Template not found**: Check file exists in `app/email-templates/src/`
2. **Compilation failed**: Check MJML syntax and variable names
3. **Missing variables**: Ensure all template variables are provided in data
4. **Cache issues**: Clear cache using API endpoint or restart service

### Error Handling

The system includes graceful error handling:
- MJML compilation errors fall back to basic HTML
- Missing template variables are logged but don't fail email sending
- Network issues with external email services are retried

## Future Enhancements

- [ ] MJML CLI automatic installation
- [ ] Template versioning and rollback
- [ ] A/B testing for email templates
- [ ] Template performance analytics
- [ ] Visual template editor integration
- [ ] Multi-language template support
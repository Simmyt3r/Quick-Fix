# QuickFix Nearby - Professional Service Marketplace

A modern, deployment-ready marketplace platform connecting customers with verified service professionals across Nigeria.

## Overview

QuickFix Nearby is built with a blue-green design system and provides:

- **24/7 Service Booking**: Customers can request services anytime
- **Verified Professionals**: Pre-vetted service providers across multiple categories
- **Real-time Management**: Live dashboard for service tracking and management
- **Enterprise Security**: Full identity verification, secure payments, and audit trails

## Technology Stack

- **Backend**: PHP 7.4+ (Server-side rendering)
- **Frontend**: HTML5, TailwindCSS, JavaScript
- **Features**: PWA-ready, Mobile-optimized, Accessible (WCAG 2.1)
- **Database**: MySQL/MariaDB schema included in `db.sql`

## Features

### Core Capabilities

1. **Customer Booking**
   - Location-based service requests
   - Service category selection
   - Urgency level specification
   - Schedule preferences

2. **Provider Management**
   - Comprehensive professional profiles
   - Availability management
   - Territory coverage mapping
   - Ratings and earnings tracking
   - Identity verification

3. **Admin Controls**
   - Lead review and management
   - Provider approval workflow
   - Incident tracking
   - Payment reconciliation
   - Detailed reporting

### Service Categories

- ⚡ Electrician
- 🚰 Plumber
- 🚗 Mechanic
- 🧱 Builder
- 💈 Barber
- And more...

## Installation

### Requirements

- PHP 7.4 or higher
- Web server (Apache/Nginx)
- HTTPS certificate (production)

### Setup

1. Clone the repository
```bash
git clone https://github.com/Silabs-Co-Technologies-Ltd/QuickFix.git
cd QuickFix
```

2. Configure your web server to serve the directory

3. Create the database and load the Version 2.0 schema
```bash
mysql -u <user> -p quickfix_db < db.sql
```

4. Set environment variables
```bash
export APP_ENV=production
```

5. Ensure `sessions` directory is writable for PHP sessions

## Deployment

### Local Development

```bash
php -S localhost:8000
```

Visit `http://localhost:8000` in your browser.

### Production Deployment

1. **Environment Configuration**
   - Set `APP_ENV=production`
   - Disable error display: `display_errors = 0`
   - Enable error logging to file

2. **Security Headers**
   - HTTPS enforced (included in code)
   - CSP headers configured
   - XSS protection enabled
   - Clickjacking protection via X-Frame-Options

3. **Database Integration**
   - Import `db.sql` into MySQL/MariaDB
   - Configure `DB_HOST`, `DB_USER`, `DB_PASS`, and `DB_NAME`
   - Use the included tables for users, customers, professionals, service requests, contact submissions, and remember tokens

4. **Email Configuration**
   - Configure SMTP for form submissions
   - Uncomment mail() function in index.php
   - Set admin email address

## File Structure

```
QuickFix/
├── index.php              # Main landing page (PHP)
├── index.html             # Static HTML version
├── db.sql                 # Version 2.0 MySQL/MariaDB schema
├── manifest.webmanifest   # PWA manifest
├── sw.js                  # Service Worker
├── logo.png              # Brand logo
└── README.md             # This file
```

## Security Features

- CSRF token protection on forms
- Input sanitization and validation
- Secure headers (CSP, X-Frame-Options, etc.)
- Session management with secure tokens
- Error handling without exposing system details
- SQL injection prevention ready

## Accessibility

- WCAG 2.1 Level AA compliant
- Keyboard navigation support
- Focus indicators on interactive elements
- ARIA labels for screen readers
- Reduced motion support
- Color contrast ratios > 4.5:1

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Color Scheme

- **Deep Blue**: `#003d82`
- **Bright Green**: `#00b896`
- **Light Blue**: `#e8f4f8`
- **Dark Blue**: `#001f41`

## Performance

- Optimized TailwindCSS (CDN)
- Service Worker caching strategy
- Responsive images
- Minimal JavaScript
- Fast LCP, FID, CLS metrics

## Development

### Adding New Features

1. Update HTML structure in `index.php`
2. Add TailwindCSS classes (no additional CSS needed)
3. Add PHP logic as needed
4. Test with both desktop and mobile browsers

### Testing Form Submission

The contact form is configured for local testing. In production:

1. Configure your email service
2. Update the `mail()` function with admin email
3. Implement database storage if needed

## Future Enhancements

- [x] Version 2.0 database schema for users, customers, providers, bookings, contacts, and remember tokens
- [ ] User authentication system
- [ ] Payment gateway integration
- [ ] Real-time notifications
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Analytics dashboard

## Support

For issues, feature requests, or questions:
- GitHub Issues: [Project Issues](https://github.com/Silabs-Co-Technologies-Ltd/QuickFix/issues)
- Email: support@quickfix.ng

## License

MIT License - See LICENSE file for details

## Credits

Built with ❤️ for Nigeria 🇳🇬

**Founder**: Nicazz Ishor

---

**Last Updated**: June 2026
**Version**: 2.0.0
**Status**: Production Ready

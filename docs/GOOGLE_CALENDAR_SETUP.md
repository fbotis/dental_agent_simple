# Google Calendar Integration Setup Guide

This guide explains how to configure the GoogleCalendarAppointmentSystem to work with your Google Calendar.

## Prerequisites

- A Google account with Google Calendar
- Python 3.8 or higher
- Required packages: `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### 2. Enable Google Calendar API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google Calendar API"
3. Click on it and press **Enable**

### 3. Create Service Account Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Fill in the service account details:
   - Name: `dental-clinic-calendar` (or any name you prefer)
   - Description: "Service account for dental clinic appointment system"
4. Click **Create and Continue**
5. Skip the optional grant access steps (click **Continue** then **Done**)
6. Click on the newly created service account
7. Go to the **Keys** tab
8. Click **Add Key** > **Create new key**
9. Select **JSON** format
10. Click **Create** - this will download the JSON credentials file
11. Save this file as `service-account-credentials.json` in the `examples/dental_clinic/` directory

### 4. Share Your Calendar with the Service Account

**Important:** The service account needs access to your calendar to create/read/update/delete events.

1. Open the downloaded JSON credentials file
2. Find the `client_email` field (looks like: `dental-clinic-calendar@your-project.iam.gserviceaccount.com`)
3. Copy this email address
4. Open [Google Calendar](https://calendar.google.com)
5. Find your calendar in the left sidebar
6. Click the three dots next to it > **Settings and sharing**
7. Scroll to **Share with specific people**
8. Click **Add people**
9. Paste the service account email
10. Set permissions to **Make changes to events**
11. Click **Send**

### 5. Configure the Test Script

Edit the `test_google_calendar.py` file:

```python
# Update calendar configuration
calendar_config = {
    "main": "primary",  # Use "primary" for your main calendar or calendar ID
    "doctors": {
        "Dr. Ana Popescu": "your-email@gmail.com",  # Replace with your Gmail address
    }
}
```

If you want to use a specific calendar (not your primary):
1. In Google Calendar settings, scroll to **Integrate calendar**
2. Copy the **Calendar ID**
3. Replace `"primary"` with this Calendar ID

### 6. Set Environment Variable (Optional)

You can set the service account file path via environment variable:

```bash
export GOOGLE_SERVICE_ACCOUNT_FILE="/path/to/service-account-credentials.json"
```

Or just ensure the file is named `service-account-credentials.json` in the same directory as the test script.

## Running the Tests

```bash
cd examples/dental_clinic
python test_google_calendar.py
```

## Configuration Options

### Calendar Configuration Structure

```python
calendar_config = {
    "main": "primary",  # Main calendar for all appointments
    "doctors": {
        # Doctor name : Calendar ID or email
        "Dr. Ana Popescu": "ana.popescu@clinica.ro",
        "Dr. Mihai Ionescu": "mihai.ionescu@clinica.ro",
        "Dr. Maria Georgescu": "maria.georgescu@clinica.ro"
    }
}
```

### Service Account File Location

Option 1: Default location (same directory):
```python
system = GoogleCalendarAppointmentSystem(
    service_account_file="service-account-credentials.json",
    calendar_config=calendar_config
)
```

Option 2: Absolute path:
```python
system = GoogleCalendarAppointmentSystem(
    service_account_file="/path/to/credentials.json",
    calendar_config=calendar_config
)
```

Option 3: Environment variable:
```bash
export GOOGLE_SERVICE_ACCOUNT_FILE="/path/to/credentials.json"
```

## Troubleshooting

### Error: "Service account file required"
- Ensure the credentials JSON file exists at the specified path
- Check the file path is correct

### Error: "Invalid credentials"
- Verify the JSON file is valid and complete
- Ensure you downloaded the key in JSON format

### Error: "Calendar not found" or "Insufficient permissions"
- Verify you shared the calendar with the service account email
- Check the service account has "Make changes to events" permission
- Wait a few minutes after sharing for permissions to propagate

### No events appearing
- Verify the calendar ID is correct (`"primary"` for main calendar)
- Check the service account email in calendar sharing settings
- Ensure the time zone is correct (default: Europe/Bucharest)

### API quota exceeded
- Google Calendar API has rate limits
- Free tier: 1,000,000 queries per day
- If exceeded, wait or request quota increase in Google Cloud Console

## Security Best Practices

1. **Never commit** the `service-account-credentials.json` file to version control
2. Add it to `.gitignore`:
   ```
   service-account-credentials.json
   *-credentials.json
   ```
3. Store credentials securely in production (use secret management services)
4. Rotate service account keys periodically
5. Grant minimum necessary permissions

## Integration with Dental Clinic Assistant

Once configured, use it in your application:

```python
from appointment_systems import GoogleCalendarAppointmentSystem

# Initialize
appointment_system = GoogleCalendarAppointmentSystem(
    service_account_file="service-account-credentials.json",
    calendar_config={
        "main": "primary",
        "doctors": {
            "Dr. Ana Popescu": "your-email@gmail.com"
        }
    }
)

# Use in your flow
# See dental_clinic_assistant.py for full integration
```

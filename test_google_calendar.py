#!/usr/bin/env python3
"""
Test script for GoogleCalendarAppointmentSystem.

This script tests all methods of the Google Calendar integration.
Run with: python test_google_calendar.py
"""

import os
from datetime import datetime, timedelta
from appointment_systems import GoogleCalendarAppointmentSystem


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def main():
    # Configuration
    SERVICE_ACCOUNT_FILE = os.getenv(
        'GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account-credentials.json')

    # Your calendar configuration
    calendar_config = {
        "doctors": {
            # Replace with your actual doctor calendars
            "Dr. Ana Popescu": "b521ff85c43bc6e250383db80a655b39091e4cb0df89b057912ee6665f95abac@group.calendar.google.com",
            "Dr. Mihai Ionescu": "6918066189269a9170688088e2137fced2003960dd8e42f227c1fb0f79faeb94@group.calendar.google.com"
        }
    }

    print_section("Initializing Google Calendar System")

    try:
        system = GoogleCalendarAppointmentSystem(
            service_account_file=SERVICE_ACCOUNT_FILE,
            calendar_config=calendar_config
        )
        print("✓ Google Calendar system initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # Test data
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    test_date = tomorrow
    test_time = "14:00"

    # Test 1: Check Availability
    print_section("Test 1: Check Availability")
    is_available = system.check_availability(
        date=test_date,
        time=test_time,
        duration_minutes=60
    )
    print(f"Is {test_time} on {test_date} available? {is_available}")

    # Test 2: Get Available Slots
    print_section("Test 2: Get Available Slots")
    slots = system.get_available_slots(date=test_date)
    print(f"Available slots for {test_date}:")
    for slot in slots:
        print(f"  - {slot}")

    # Test 3: Create Appointment
    print_section("Test 3: Create Appointment")
    appointment_id = system.create_appointment(
        patient_name="John Doe",
        phone="+40712345678",
        date=test_date,
        time=test_time,
        service="teeth_cleaning",
        dentist="Dr. Ana Popescu"
    )

    if appointment_id:
        print(f"✓ Appointment created successfully!")
        print(f"  Appointment ID: {appointment_id}")
    else:
        print("✗ Failed to create appointment")
        return

    # Test 4: Find Appointment
    print_section("Test 4: Find Appointment")
    found = system.find_appointment(patient_name="John Doe")
    if found:
        print("✓ Appointment found:")
        print(f"  ID: {found.get('id')}")
        print(f"  Patient: {found.get('patient_name')}")
        print(f"  Date: {found.get('date')}")
        print(f"  Time: {found.get('time')}")
        print(f"  Service: {found.get('service')}")
        print(f"  Dentist: {found.get('dentist')}")
    else:
        print("✗ Appointment not found")

    # Test 5: Update Appointment
    print_section("Test 5: Update Appointment")
    new_time = "15:00"
    success = system.update_appointment(
        appointment_id=appointment_id,
        date=test_date,
        time=new_time
    )

    if success:
        print(f"✓ Appointment updated successfully to {new_time}")
    else:
        print("✗ Failed to update appointment")

    # Test 6: Check Updated Availability
    print_section("Test 6: Verify Updated Slot")
    # Check if old time is now available
    old_available = system.check_availability(date=test_date, time=test_time)
    print(f"Is old time {test_time} now available? {old_available}")

    # Check if new time is now busy
    new_available = system.check_availability(date=test_date, time=new_time)
    print(f"Is new time {new_time} now available? {new_available}")

    # Test 7: Cancel Appointment
    print_section("Test 7: Cancel Appointment")
    user_input = input(
        f"Do you want to cancel the test appointment? (yes/no): ")

    if user_input.lower() in ['yes', 'y']:
        success = system.cancel_appointment(appointment_id)
        if success:
            print("✓ Appointment cancelled successfully")

            # Verify cancellation
            found_after_cancel = system.find_appointment(
                patient_name="John Doe")
            if not found_after_cancel:
                print("✓ Verified: Appointment no longer found")
            else:
                print("⚠ Warning: Appointment still appears in search")
        else:
            print("✗ Failed to cancel appointment")
    else:
        print(
            f"⚠ Skipped cancellation. Please manually remove appointment ID: {appointment_id}")

    print_section("All Tests Completed")


if __name__ == "__main__":
    main()

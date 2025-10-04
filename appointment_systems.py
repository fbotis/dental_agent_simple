#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Appointment system implementations for the dental clinic assistant."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class AppointmentSystemInterface(ABC):
    """Abstract interface for appointment systems."""

    @abstractmethod
    def check_availability(self, date: str, time: str, duration_minutes: int = 60, doctor: str = None) -> bool:
        """Check if a time slot is available."""
        pass

    @abstractmethod
    def get_available_slots(self, date: str, doctor: str = None) -> List[str]:
        """Get available time slots for a given date."""
        pass

    @abstractmethod
    def create_appointment(self, patient_name: str, phone: str, date: str,
                           time: str, service: str, dentist: Optional[str] = None) -> Optional[str]:
        """Create a new appointment."""
        pass

    @abstractmethod
    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        pass

    @abstractmethod
    def update_appointment(self, appointment_id: str, **updates) -> bool:
        """Update an appointment."""
        pass

    @abstractmethod
    def find_appointment(self, patient_name: str, phone: Optional[str] = None) -> Optional[Dict]:
        """Find an appointment by patient name and optionally phone."""
        pass


class MockAppointmentSystem(AppointmentSystemInterface):
    """Mock appointment system for testing and development."""

    def __init__(self):
        self.appointments: Dict[str, Dict] = {}
        self.next_id = 1

    def check_availability(self, date: str, time: str, duration_minutes: int = 60, doctor: str = None) -> bool:
        """Check if a time slot is available."""
        busy_times = ["10:00 AM", "2:00 PM", "4:00 PM"]
        return time not in busy_times

    def get_available_slots(self, date: str, doctor: str = None) -> List[str]:
        """Get available time slots for a given date."""
        all_slots = [
            "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM",
            "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"
        ]
        busy_slots = ["10:00 AM", "2:00 PM", "4:00 PM"]
        return [slot for slot in all_slots if slot not in busy_slots]

    def create_appointment(self, patient_name: str, phone: str, date: str,
                           time: str, service: str, dentist: Optional[str] = None) -> Optional[str]:
        """Create a new appointment."""
        appointment_id = f"APPT{self.next_id:04d}"
        self.next_id += 1

        self.appointments[appointment_id] = {
            "id": appointment_id,
            "patient_name": patient_name,
            "phone": phone,
            "date": date,
            "time": time,
            "service": service,
            "dentist": dentist or "Dr. Ana Popescu",
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        return appointment_id

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        if appointment_id in self.appointments:
            self.appointments[appointment_id]["status"] = "cancelled"
            return True
        return False

    def update_appointment(self, appointment_id: str, **updates) -> bool:
        """Update an appointment."""
        if appointment_id in self.appointments:
            self.appointments[appointment_id].update(updates)
            return True
        return False

    def find_appointment(self, patient_name: str, phone: Optional[str] = None) -> Optional[Dict]:
        """Find an appointment by patient name and optionally phone."""
        for appt in self.appointments.values():
            if (appt["patient_name"].lower() == patient_name.lower() and
                    appt["status"] == "scheduled"):
                if phone is None or appt["phone"] == phone:
                    return appt
        return None


class GoogleCalendarAppointmentSystem(AppointmentSystemInterface):
    """Google Calendar integration for dental clinic appointments."""

    def __init__(self, service_account_file: str = None, calendar_config: dict = None):
        """Initialize Google Calendar service."""
        print(f"🔧 Initializing Google Calendar Appointment System...")
        print(f"   Service Account File: {service_account_file}")

        self.service = self._initialize_service(service_account_file)

        self.calendar_config = calendar_config or {
            "doctors": {
                "Dr. Ana Popescu": "ana.popescu@clinica.ro",
                "Dr. Mihai Ionescu": "mihai.ionescu@clinica.ro",
                "Dr. Maria Georgescu": "maria.georgescu@clinica.ro"
            }
        }

        print(f"   Doctor Calendars configured:")
        for doctor, calendar_id in self.calendar_config.get("doctors", {}).items():
            print(f"      - {doctor}: {calendar_id}")

        self.service_colors = {
            "general_dentistry": "1", "teeth_cleaning": "2", "fillings": "3",
            "root_canal": "4", "teeth_whitening": "5", "crown": "6",
            "extraction": "7", "orthodontics": "8"
        }

        self.doctor_colors = {
            "Dr. Ana Popescu": "9", "Dr. Mihai Ionescu": "10", "Dr. Maria Georgescu": "11"
        }

    def _initialize_service(self, service_account_file: str):
        """Initialize Google Calendar API service."""
        try:
            if service_account_file:
                print(f"   Loading service account credentials...")
                credentials = ServiceAccountCredentials.from_service_account_file(
                    service_account_file,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                print(f"   ✓ Credentials loaded successfully")
            else:
                raise ValueError(
                    "Service account file required for Google Calendar integration")

            print(f"   Building Google Calendar API service...")
            service = build('calendar', 'v3', credentials=credentials)
            print(f"   ✓ Google Calendar API service initialized")
            return service
        except Exception as e:
            print(f"   ✗ Error initializing Google Calendar service: {e}")
            return None

    def check_availability(self, date: str, time: str, duration_minutes: int = 60, doctor: str = None) -> bool:
        """Check if a time slot is available."""
        print(f"🔍 Checking availability: {date} at {time} (duration: {duration_minutes}min, doctor: {doctor})")

        if not self.service:
            busy_times = ["10:00", "14:00", "16:00"]
            return time not in busy_times

        try:
            start_datetime = self._parse_datetime(date, time)
            end_datetime = self._add_minutes(start_datetime, duration_minutes)

            # Check specific doctor's calendar if provided
            if doctor:
                calendar_id = self.calendar_config["doctors"].get(doctor)
                if calendar_id:
                    busy_times = self._get_busy_times(
                        calendar_id,
                        start_datetime.isoformat(),
                        end_datetime.isoformat()
                    )
                    is_available = len(busy_times) == 0
                    print(f"   {'✓ Available' if is_available else '✗ Busy'} - {doctor}")
                    return is_available
            else:
                # If no doctor specified, check all doctor calendars
                for doc_name, calendar_id in self.calendar_config["doctors"].items():
                    busy_times = self._get_busy_times(
                        calendar_id,
                        start_datetime.isoformat(),
                        end_datetime.isoformat()
                    )
                    if busy_times:
                        print(f"   ✗ Busy - {doc_name} has conflicts")
                        return False

            print(f"   ✓ Available")
            return True

        except Exception as e:
            print(f"Error checking availability: {e}")
            return False

    def get_available_slots(self, date: str, doctor: str = None) -> List[str]:
        """Get available time slots for a given date."""
        print(f"📋 Getting available slots for {date} (doctor: {doctor})")

        if not self.service:
            all_slots = ["08:00", "09:00", "10:00", "11:00",
                         "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
            busy_slots = ["10:00", "14:00", "16:00"]
            return [slot for slot in all_slots if slot not in busy_slots]

        try:
            available_slots = []
            for hour in range(8, 18):
                time_slot = f"{hour:02d}:00"
                if self.check_availability(date, time_slot, doctor=doctor):
                    available_slots.append(time_slot)

            print(f"   Found {len(available_slots)} available slots: {', '.join(available_slots)}")
            return available_slots
        except Exception as e:
            print(f"   ✗ Error getting available slots: {e}")
            return []

    def create_appointment(self, patient_name: str, phone: str, date: str,
                           time: str, service: str, dentist: str = None) -> Optional[str]:
        """Create appointment in Google Calendar."""
        if not self.service:
            return f"GCAL{hash(f'{patient_name}{date}{time}') % 10000:04d}"

        print(f"📅 Creating appointment in Google Calendar:")
        print(f"   Patient: {patient_name}")
        print(f"   Date: {date}, Time: {time}")
        print(f"   Service: {service}")
        print(f"   Dentist: {dentist}")

        try:
            try:
                from .clinic_info import ClinicInfo
            except ImportError:
                from clinic_info import ClinicInfo
            clinic_info = ClinicInfo()

            if not dentist:
                dentist = "Dr. Ana Popescu"

            service_details = clinic_info.get_service(service)
            duration = service_details.get('duration', 60)

            start_datetime = self._parse_datetime(date, time)
            end_datetime = self._add_minutes(start_datetime, duration)

            event = {
                'summary': f'{service_details.get("name", service)} - {patient_name}',
                'description': f"""
Pacient: {patient_name}
Telefon: {phone}
Serviciu: {service_details.get("name", service)}
Doctor: {dentist}
Durată: {duration} minute
Cost estimat: {service_details.get("price", "N/A")}
                """.strip(),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Bucharest',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Bucharest',
                },
                'colorId': self.service_colors.get(service, '1'),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 60},
                    ],
                },
            }

            # Create event in doctor's calendar only
            doctor_calendar_id = self.calendar_config["doctors"].get(dentist)
            if not doctor_calendar_id:
                print(f"   ✗ No calendar found for dentist: {dentist}")
                return None

            print(f"   Creating event in calendar: {doctor_calendar_id}")
            created_event = self.service.events().insert(
                calendarId=doctor_calendar_id,
                body=event
            ).execute()

            print(f"   ✓ Appointment created successfully!")
            print(f"   Event ID: {created_event['id']}")
            return created_event['id']

        except HttpError as e:
            print(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            print(f"Error creating appointment: {e}")
            return None

    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel appointment from doctor calendars."""
        print(f"🗑️  Cancelling appointment: {appointment_id}")

        if not self.service:
            return True

        try:
            # Try to delete from all doctor calendars
            deleted = False
            for doc_name, doctor_calendar in self.calendar_config["doctors"].items():
                try:
                    self.service.events().delete(
                        calendarId=doctor_calendar,
                        eventId=appointment_id
                    ).execute()
                    print(f"   ✓ Deleted from {doc_name}'s calendar")
                    deleted = True
                    break  # Successfully deleted, stop trying
                except HttpError as e:
                    # Event doesn't exist in this calendar, try next
                    if e.resp.status == 404:
                        continue
                    else:
                        print(f"   ✗ Error deleting from {doc_name}: {e}")

            if not deleted:
                print(f"   ✗ Appointment not found in any calendar")
            return deleted
        except Exception as e:
            print(f"   ✗ Error cancelling appointment: {e}")
            return False

    def update_appointment(self, appointment_id: str, **updates) -> bool:
        """Update appointment in doctor calendars."""
        print(f"✏️  Updating appointment: {appointment_id}")
        print(f"   Updates: {updates}")

        if not self.service:
            return True

        try:
            # Find which doctor calendar has this event
            event = None
            calendar_id = None
            for doc_name, doc_calendar in self.calendar_config["doctors"].items():
                try:
                    event = self.service.events().get(
                        calendarId=doc_calendar,
                        eventId=appointment_id
                    ).execute()
                    calendar_id = doc_calendar
                    print(f"   Found in {doc_name}'s calendar")
                    break
                except HttpError as e:
                    if e.resp.status == 404:
                        continue
                    else:
                        raise

            if not event:
                print(f"   ✗ Appointment {appointment_id} not found in any doctor calendar")
                return False

            if 'date' in updates and 'time' in updates:
                start_datetime = self._parse_datetime(
                    updates['date'], updates['time'])
                current_duration = self._get_event_duration(event)
                end_datetime = self._add_minutes(
                    start_datetime, current_duration)

                event['start']['dateTime'] = start_datetime.isoformat()
                event['end']['dateTime'] = end_datetime.isoformat()

            self.service.events().update(
                calendarId=calendar_id,
                eventId=appointment_id,
                body=event
            ).execute()

            print(f"   ✓ Appointment updated successfully")
            return True
        except Exception as e:
            print(f"   ✗ Error updating appointment: {e}")
            return False

    def find_appointment(self, patient_name: str, phone: str = None) -> Optional[dict]:
        """Find appointment by patient name."""
        print(f"🔎 Finding appointment for: {patient_name} (phone: {phone})")

        if not self.service:
            return None

        try:
            # Search across all doctor calendars
            all_events = []
            for doc_name, doctor_calendar in self.calendar_config["doctors"].items():
                try:
                    events_result = self.service.events().list(
                        calendarId=doctor_calendar,
                        q=patient_name,
                        timeMin=datetime.now().isoformat() + 'Z',
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    events = events_result.get('items', [])
                    if events:
                        print(f"   Found {len(events)} event(s) in {doc_name}'s calendar")
                    all_events.extend(events)
                except HttpError:
                    continue

            events = all_events

            for event in events:
                if patient_name.lower() in event.get('summary', '').lower():
                    # Parse the datetime properly considering timezone
                    start_dt_str = event['start'].get('dateTime', '')
                    if start_dt_str:
                        # Parse ISO format and convert to local time
                        start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
                        date_str = start_dt.strftime('%Y-%m-%d')
                        time_str = start_dt.strftime('%H:%M')
                    else:
                        date_str = event['start'].get('dateTime', '').split('T')[0]
                        time_str = event['start'].get('dateTime', '').split('T')[1][:5]

                    result = {
                        'id': event['id'],
                        'patient_name': patient_name,
                        'date': date_str,
                        'time': time_str,
                        'service': event.get('summary', '').split(' - ')[0],
                        'dentist': self._extract_doctor_from_description(event.get('description', '')),
                        'status': 'scheduled'
                    }
                    print(f"   ✓ Found appointment: {date_str} at {time_str}")
                    return result

            print(f"   ✗ No appointment found")
            return None
        except Exception as e:
            print(f"   ✗ Error finding appointment: {e}")
            return None

    def _parse_datetime(self, date: str, time: str):
        """Parse date and time strings into datetime object."""
        return datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")

    def _add_minutes(self, dt, minutes: int):
        """Add minutes to datetime object."""
        return dt + timedelta(minutes=minutes)

    def _get_busy_times(self, calendar_id: str, start_time: str, end_time: str):
        """Get busy times for a calendar in the specified time range."""
        try:
            # Ensure timestamps are in proper RFC3339 format with timezone
            if not start_time.endswith('Z') and '+' not in start_time:
                start_time = start_time + 'Z'
            if not end_time.endswith('Z') and '+' not in end_time:
                end_time = end_time + 'Z'

            freebusy_query = {
                'timeMin': start_time,
                'timeMax': end_time,
                'items': [{'id': calendar_id}]
            }

            freebusy_result = self.service.freebusy().query(body=freebusy_query).execute()
            busy_times = freebusy_result['calendars'][calendar_id].get(
                'busy', [])

            return busy_times
        except Exception as e:
            print(f"Error getting busy times: {e}")
            return []

    def _get_event_duration(self, event):
        """Get duration of event in minutes."""
        start = datetime.fromisoformat(
            event['start']['dateTime'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(
            event['end']['dateTime'].replace('Z', '+00:00'))
        return int((end - start).total_seconds() / 60)

    def _extract_doctor_from_description(self, description: str) -> str:
        """Extract doctor name from event description."""
        for line in description.split('\n'):
            if line.startswith('Doctor:'):
                return line.split('Doctor:')[1].strip()
        return "Dr. Ana Popescu"


class AppointmentSystemFactory:
    """Factory for creating appointment systems."""

    @staticmethod
    def create_system(system_type: str = "mock", **kwargs) -> AppointmentSystemInterface:
        """Create an appointment system instance."""
        if system_type == "mock":
            return MockAppointmentSystem()
        elif system_type == "google_calendar":
            return GoogleCalendarAppointmentSystem(**kwargs)
        else:
            raise ValueError(f"Unknown appointment system type: {system_type}")

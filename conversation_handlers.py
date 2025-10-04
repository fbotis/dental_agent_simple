#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Conversation handlers for the dental clinic assistant."""

from typing import Dict, Optional, Tuple, List
from pipecat_flows import FlowManager, NodeConfig
try:
    from .clinic_info import ClinicInfo
    from .appointment_systems import AppointmentSystemInterface
    from .flow_nodes import FlowNodeFactory
except ImportError:
    from clinic_info import ClinicInfo
    from appointment_systems import AppointmentSystemInterface
    from flow_nodes import FlowNodeFactory


class ConversationState:
    """Manages conversation state data."""

    def __init__(self):
        self.current_appointment: Optional[str] = None
        self.patient_info: Dict = {}
        self.found_appointment: Dict = {}
        self.available_slots: List[str] = []

    def reset(self):
        """Reset conversation state."""
        self.current_appointment = None
        self.patient_info = {}
        self.found_appointment = {}
        self.available_slots = []


class ConversationHandlers:
    """Centralized conversation handlers to avoid circular imports."""

    def __init__(self, clinic_info: ClinicInfo, appointment_system: AppointmentSystemInterface,
                 node_factory: FlowNodeFactory, conversation_state: ConversationState):
        self.clinic_info = clinic_info
        self.appointment_system = appointment_system
        self.node_factory = node_factory
        self.conversation_state = conversation_state

    # Information handlers
    async def get_clinic_info(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """User wants general clinic information."""
        functions = [
            self.get_services_info, self.get_dentist_info,
            self.schedule_appointment, self.back_to_main
        ]
        return None, self.node_factory.create_info_node(functions)

    async def get_services_info(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """User wants information about dental services."""
        # Check if we're in the middle of booking (patient info exists)
        if self.conversation_state.patient_info.get("name"):
            # During booking flow - allow return to service selection
            functions = [
                self.return_to_service_selection, self.select_service, self.back_to_main
            ]
        else:
            # General info request - standard navigation
            functions = [
                self.get_clinic_info, self.get_dentist_info,
                self.schedule_appointment, self.back_to_main
            ]
        return None, self.node_factory.create_services_node(functions)

    async def get_dentist_info(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """User wants information about dentists."""
        functions = [
            self.get_clinic_info, self.get_services_info,
            self.schedule_appointment, self.back_to_main
        ]
        return None, self.node_factory.create_dentist_node(functions)

    # Appointment scheduling handlers

    async def handle_symptoms(self, flow_manager: FlowManager, symptoms_description: str) -> Tuple[None, NodeConfig]:
        """Handle symptom-based triage - analyze symptoms and suggest appropriate service."""
        # Detect symptoms and get recommended service
        symptom_match = self.clinic_info.detect_symptoms(symptoms_description)

        if symptom_match:
            # Store the detected symptom info
            self.conversation_state.patient_info["detected_symptom"] = symptom_match
            self.conversation_state.patient_info["service"] = symptom_match["service"]

            # Check if we already have patient info (name and phone)
            has_patient_info = (
                self.conversation_state.patient_info.get("name") and
                self.conversation_state.patient_info.get("phone")
            )

            # If we already have patient info, skip straight to date/time selection
            if has_patient_info:
                print(f"✅ Patient info already exists, skipping to date/time selection")
                functions = [self.select_date_time, self.back_to_main]
                return None, self.node_factory.create_date_time_selection_node(functions)

            # Otherwise, show symptom triage and ask for patient info
            if symptom_match["priority"] == "urgent":
                functions = [self.provide_patient_info,
                             self.get_clinic_info, self.back_to_main]
                return None, self.node_factory.create_symptom_triage_node(
                    functions, symptom_match, is_urgent=True
                )
            else:
                # Normal priority - suggest service and offer booking
                functions = [self.provide_patient_info,
                             self.get_services_info, self.back_to_main]
                return None, self.node_factory.create_symptom_triage_node(
                    functions, symptom_match, is_urgent=False
                )
        else:
            # No symptoms detected - go to general scheduling
            functions = [self.provide_patient_info,
                         self.get_services_info, self.back_to_main]
            return None, self.node_factory.create_appointment_node(functions)

    async def schedule_appointment(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """User wants to schedule a new appointment."""
        functions = [self.provide_patient_info,
                     self.handle_symptoms, self.back_to_main]
        return None, self.node_factory.create_appointment_node(functions)

    async def provide_patient_info(self, flow_manager: FlowManager,
                                   patient_name: str, phone_number: str) -> Tuple[None, NodeConfig]:
        """Collect patient name and phone for appointment scheduling."""
        self.conversation_state.patient_info = {
            "name": patient_name,
            "phone": phone_number
        }

        # If we already have a service from symptom triage, skip to date/time selection
        if self.conversation_state.patient_info.get("service"):
            functions = [self.select_date_time, self.back_to_main]
            return None, self.node_factory.create_date_time_selection_node(functions)

        functions = [self.select_service, self.get_services_info,
                     self.handle_symptoms, self.back_to_main]
        return None, self.node_factory.create_service_selection_node(functions)

    async def return_to_service_selection(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """Return to service selection (used after viewing services info during booking)."""
        functions = [self.select_service,
                     self.get_services_info, self.back_to_main]
        return None, self.node_factory.create_service_selection_node(functions)

    async def select_service(self, flow_manager: FlowManager, service_type: str, preferred_doctor: Optional[str] = None) -> Tuple[None, NodeConfig]:
        """Patient selects the dental service they need, optionally with a preferred doctor."""
        self.conversation_state.patient_info["service"] = service_type

        # Store preferred doctor if provided
        if preferred_doctor:
            self.conversation_state.patient_info["preferred_doctor"] = preferred_doctor
            print(f"✅ Preferred doctor selected: {preferred_doctor}")

        functions = [self.select_date_time, self.select_doctor, self.back_to_main]
        return None, self.node_factory.create_date_time_selection_node(functions)

    async def select_date_time(self, flow_manager: FlowManager,
                               preferred_date: str, preferred_time: str) -> Tuple[None, NodeConfig]:
        """Patient selects preferred date and time for appointment."""
        # Get preferred doctor if specified
        preferred_doctor = self.conversation_state.patient_info.get("preferred_doctor")

        # Check availability considering doctor preference
        if self.appointment_system.check_availability(preferred_date, preferred_time, doctor=preferred_doctor):
            self.conversation_state.patient_info["date"] = preferred_date
            self.conversation_state.patient_info["time"] = preferred_time
            functions = [self.confirm_appointment,
                         self.modify_appointment_details, self.back_to_main]
            return None, self.node_factory.create_appointment_confirmation_node(functions)
        else:
            # Get available slots for the preferred doctor
            available_slots = self.appointment_system.get_available_slots(
                preferred_date, doctor=preferred_doctor)
            self.conversation_state.available_slots = available_slots
            functions = [self.select_alternative_time,
                         self.select_date_time, self.select_doctor, self.back_to_main]
            return None, self.node_factory.create_alternative_times_node(functions)

    async def select_doctor(self, flow_manager: FlowManager, doctor_name: str) -> Tuple[None, NodeConfig]:
        """Patient selects or changes their preferred doctor."""
        self.conversation_state.patient_info["preferred_doctor"] = doctor_name
        print(f"✅ Doctor preference updated: {doctor_name}")

        # If we already have a date/time selected, re-check availability with new doctor
        if self.conversation_state.patient_info.get("date") and self.conversation_state.patient_info.get("time"):
            date = self.conversation_state.patient_info["date"]
            time = self.conversation_state.patient_info["time"]

            # Re-check availability with the new doctor
            if self.appointment_system.check_availability(date, time, doctor=doctor_name):
                functions = [self.confirm_appointment,
                             self.modify_appointment_details, self.back_to_main]
                return None, self.node_factory.create_appointment_confirmation_node(functions)
            else:
                # Show alternative times for this doctor
                available_slots = self.appointment_system.get_available_slots(date, doctor=doctor_name)
                self.conversation_state.available_slots = available_slots
                functions = [self.select_alternative_time,
                             self.select_date_time, self.back_to_main]
                return None, self.node_factory.create_alternative_times_node(functions)
        else:
            # No date/time selected yet, go to date/time selection
            functions = [self.select_date_time, self.back_to_main]
            return None, self.node_factory.create_date_time_selection_node(functions)

    async def select_alternative_time(self, flow_manager: FlowManager,
                                      selected_time: str) -> Tuple[None, NodeConfig]:
        """Patient selects an alternative time from available slots."""
        self.conversation_state.patient_info["time"] = selected_time
        functions = [self.confirm_appointment,
                     self.modify_appointment_details, self.back_to_main]
        return None, self.node_factory.create_appointment_confirmation_node(functions)

    async def confirm_appointment(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """Patient confirms appointment details and proceeds with booking."""
        patient_info = self.conversation_state.patient_info

        print(f"🔔 CONFIRMING APPOINTMENT:")
        print(f"   Name: {patient_info.get('name')}")
        print(f"   Phone: {patient_info.get('phone')}")
        print(f"   Service: {patient_info.get('service')}")
        print(f"   Date: {patient_info.get('date')}")
        print(f"   Time: {patient_info.get('time')}")

        appointment_id = self.appointment_system.create_appointment(
            patient_name=patient_info["name"],
            phone=patient_info["phone"],
            date=patient_info["date"],
            time=patient_info["time"],
            service=patient_info["service"],
            dentist=patient_info.get("preferred_doctor")
        )

        print(f"📝 Appointment ID received: {appointment_id}")

        if not appointment_id:
            print(f"❌ ERROR: Appointment creation failed!")

        self.conversation_state.current_appointment = appointment_id
        # Don't provide end_conversation yet - only after user responds to "Mai este ceva?"
        functions = [self.schedule_appointment, self.get_clinic_info,
                     self.get_services_info, self.appointment_complete]

        print(f"✅ Transitioning to appointment_success node")
        return None, self.node_factory.create_appointment_success_node(functions)

    async def modify_appointment_details(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """Patient wants to change some details before confirmation."""
        functions = [self.select_service, self.back_to_main]
        return None, self.node_factory.create_service_selection_node(functions)

    async def appointment_complete(self, flow_manager: FlowManager, needs_help: bool) -> Tuple[None, NodeConfig]:
        """Handle user response to 'Mai este ceva cu care vă pot ajuta?'"""
        print(f"📋 User needs additional help: {needs_help}")

        if needs_help:
            # User needs more help - go back to main menu
            functions = [self.schedule_appointment, self.get_services_info,
                         self.get_clinic_info, self.manage_existing_appointment]
            return None, self.node_factory.create_main_menu_node(functions)
        else:
            # User is done - now we can end conversation
            functions = [self.end_conversation]
            return None, self.node_factory.create_goodbye_node(functions)

    # Existing appointment management handlers
    async def manage_existing_appointment(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """User wants to manage an existing appointment."""
        functions = [self.find_existing_appointment, self.back_to_main]
        return None, self.node_factory.create_manage_appointment_node(functions)

    async def find_existing_appointment(self, flow_manager: FlowManager,
                                        patient_name: str,
                                        phone_number: Optional[str] = None) -> Tuple[None, NodeConfig]:
        """Find existing appointment using patient name and optionally phone."""
        appointment = self.appointment_system.find_appointment(
            patient_name, phone_number)
        if appointment:
            self.conversation_state.current_appointment = appointment["id"]
            self.conversation_state.found_appointment = appointment
            functions = [self.cancel_existing_appointment,
                         self.reschedule_existing_appointment, self.back_to_main]
            return None, self.node_factory.create_existing_appointment_options_node(functions)
        else:
            functions = [self.find_existing_appointment,
                         self.schedule_appointment, self.back_to_main]
            return None, self.node_factory.create_appointment_not_found_node(functions)

    async def cancel_existing_appointment(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """Cancel the found existing appointment."""
        appointment_id = self.conversation_state.current_appointment
        if appointment_id and self.appointment_system.cancel_appointment(appointment_id):
            functions = [self.schedule_appointment,
                         self.get_clinic_info, self.end_conversation]
            return None, self.node_factory.create_cancellation_success_node(functions)
        else:
            functions = [self.back_to_main, self.end_conversation]
            return None, self.node_factory.create_cancellation_error_node(functions)

    async def reschedule_existing_appointment(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """Reschedule the found existing appointment."""
        functions = [self.update_reschedule, self.back_to_main]
        return None, self.node_factory.create_reschedule_node(functions)

    async def update_reschedule(self, flow_manager: FlowManager,
                                new_date: str, new_time: str) -> Tuple[None, NodeConfig]:
        """Update appointment with new date and time."""
        appointment_id = self.conversation_state.current_appointment
        if appointment_id and self.appointment_system.check_availability(new_date, new_time):
            self.appointment_system.update_appointment(
                appointment_id, date=new_date, time=new_time)
            functions = [self.schedule_appointment,
                         self.get_clinic_info, self.end_conversation]
            return None, self.node_factory.create_reschedule_success_node(functions)
        else:
            available_slots = self.appointment_system.get_available_slots(
                new_date)
            self.conversation_state.available_slots = available_slots
            functions = [self.update_reschedule, self.back_to_main]
            return None, self.node_factory.create_reschedule_alternative_times_node(functions)

    # Navigation handlers
    async def back_to_main(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """User wants to return to main menu or ask something else."""
        functions = [
            self.get_clinic_info, self.get_services_info, self.get_dentist_info,
            self.schedule_appointment, self.manage_existing_appointment, self.handle_symptoms
        ]
        return None, self.node_factory.create_initial_node(functions)

    async def end_conversation(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """End conversation politely."""
        return None, self.node_factory.create_end_node([])

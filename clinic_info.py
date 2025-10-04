#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Clinic information management for the dental clinic assistant."""

from typing import Dict, List


class ClinicInfo:
    """Manages clinic information including services, dentists, and contact details."""

    def __init__(self):
        # Symptom-to-service mapping for intelligent triage
        self.symptom_mapping = {
            "urgent": {
                "keywords": ["durere", "dureri", "doare", "sângerează", "sângerare", "accident", "urgent", "fractură", "lovit", "căzut"],
                "service": "general_dentistry",
                "priority": "urgent",
                "message": "Înțeleg că aveți o situație urgentă. Vă recomand o consultație de urgență cât mai curând posibil."
            },
            "pain": {
                "keywords": ["durere", "dureri", "doare", "sensibil", "sensibilitate"],
                "service": "general_dentistry",
                "priority": "high",
                "message": "Pentru durerea dentară, vă recomand o consultație generală pentru a evalua cauza și a stabili tratamentul."
            },
            "cavity": {
                "keywords": ["carie", "cavitate", "gaură", "spărt", "deteriorat", "rupt"],
                "service": "fillings",
                "priority": "medium",
                "message": "Pentru cariile dentare sau dinții deteriorați, vă recomand o plombă dentară."
            },
            "cosmetic": {
                "keywords": ["alb", "albire", "pete", "decolorat", "galben", "estetic", "frumos"],
                "service": "teeth_whitening",
                "priority": "low",
                "message": "Pentru îmbunătățirea aspectului dinților, vă recomand un tratament de albire dentară."
            },
            "cleaning": {
                "keywords": ["curățare", "detartraj", "tartru", "igienă", "periaj", "control"],
                "service": "teeth_cleaning",
                "priority": "low",
                "message": "Pentru igienă dentară și prevenție, vă recomand un detartraj profesional."
            },
            "orthodontic": {
                "keywords": ["strâmb", "înclinat", "aparat", "aliniament", "drept", "ortodonție"],
                "service": "orthodontics",
                "priority": "low",
                "message": "Pentru problemele de aliniament dentar, vă recomand o consultație ortodontică."
            },
            "extraction": {
                "keywords": ["extracție", "scoate", "îndepărtare", "minte", "înțelepciune"],
                "service": "extraction",
                "priority": "medium",
                "message": "Pentru extracția dentară, vă pot programa cu unul dintre doctorii noștri."
            },
            "crown": {
                "keywords": ["coroană", "capiș", "restaurare", "refacere"],
                "service": "crown",
                "priority": "medium",
                "message": "Pentru restaurarea dinților deteriorați, vă recomand o coroană dentară."
            },
            "root_canal": {
                "keywords": ["canal", "endodontic", "nerv", "infecție", "abces"],
                "service": "root_canal",
                "priority": "high",
                "message": "Pentru tratamentul canalului radicular, vă recomand o consultație endodontică."
            }
        }

        self._info = {
            "name": "Clinica Dentară Zâmbet Strălucitor",
            "address": "Strada Dentară nr. 123, Sector 1, București 010123",
            "phone": "0721-DINTI (0721-346-848)",
            "email": "info@zambetstralucitor.ro",
            "hours": {
                "monday": "08:00 - 18:00",
                "tuesday": "08:00 - 18:00",
                "wednesday": "08:00 - 18:00",
                "thursday": "08:00 - 18:00",
                "friday": "08:00 - 16:00",
                "saturday": "09:00 - 14:00",
                "sunday": "Închis"
            },
            "services": {
                "general_dentistry": {
                    "name": "Stomatologie Generală",
                    "description": "Curățări de rutină, controale și îngrijire preventivă",
                    "duration": 60,
                    "price": "300 RON"
                },
                "teeth_cleaning": {
                    "name": "Detartraj Dentar",
                    "description": "Curățare și lustruire dentară profesională",
                    "duration": 45,
                    "price": "200 RON"
                },
                "fillings": {
                    "name": "Plombe Dentare",
                    "description": "Tratamentul cariilor cu plombe din compozit sau amalgam",
                    "duration": 90,
                    "price": "400-700 RON"
                },
                "root_canal": {
                    "name": "Tratament Endodontic",
                    "description": "Tratamentul dinților infectați sau cariați sever",
                    "duration": 120,
                    "price": "1600-2400 RON"
                },
                "teeth_whitening": {
                    "name": "Albire Dentară",
                    "description": "Tratament profesional de albire a dinților",
                    "duration": 90,
                    "price": "800 RON"
                },
                "crown": {
                    "name": "Coroană Dentară",
                    "description": "Coroane personalizate pentru restaurarea dinților deteriorați",
                    "duration": 120,
                    "price": "2000-3000 RON"
                },
                "extraction": {
                    "name": "Extracție Dentară",
                    "description": "Îndepărtarea sigură a dinților deteriorați sau problematici",
                    "duration": 60,
                    "price": "300-800 RON"
                },
                "orthodontics": {
                    "name": "Consultație Ortodontică",
                    "description": "Evaluare pentru aparate dentare sau aliniatori transparenți",
                    "duration": 60,
                    "price": "200 RON"
                }
            },
            "dentists": [
                {
                    "name": "Dr. Ana Popescu",
                    "specialty": "Stomatologie Generală",
                    "experience": "15 ani",
                    "education": "Doctorat în Medicină Dentară, UMF Carol Davila"
                },
                {
                    "name": "Dr. Mihai Ionescu",
                    "specialty": "Endodonție (Specialist în Tratamente Canalare)",
                    "experience": "12 ani",
                    "education": "Doctorat în Medicină Dentară și Rezidențiat Endodonție"
                },
                {
                    "name": "Dr. Maria Georgescu",
                    "specialty": "Ortodonție",
                    "experience": "10 ani",
                    "education": "Doctorat în Medicină Dentară și Rezidențiat Ortodonție"
                }
            ],
            "emergency": "Pentru urgențe stomatologice în afara programului, sunați la 0721-URGENTA (0721-874-368)"
        }

    @property
    def name(self) -> str:
        """Get clinic name."""
        return self._info["name"]

    @property
    def address(self) -> str:
        """Get clinic address."""
        return self._info["address"]

    @property
    def phone(self) -> str:
        """Get clinic phone number."""
        return self._info["phone"]

    @property
    def email(self) -> str:
        """Get clinic email."""
        return self._info["email"]

    @property
    def hours(self) -> Dict[str, str]:
        """Get clinic operating hours."""
        return self._info["hours"]

    @property
    def services(self) -> Dict[str, Dict]:
        """Get available services."""
        return self._info["services"]

    @property
    def dentists(self) -> List[Dict]:
        """Get dentist information."""
        return self._info["dentists"]

    @property
    def emergency(self) -> str:
        """Get emergency contact information."""
        return self._info["emergency"]

    def get_service(self, service_key: str) -> Dict:
        """Get specific service information."""
        return self._info["services"].get(service_key, {})

    def get_dentist_by_name(self, name: str) -> Dict:
        """Get dentist information by name."""
        for dentist in self._info["dentists"]:
            if dentist["name"] == name:
                return dentist
        return {}

    def get_services_text(self) -> str:
        """Get formatted services text."""
        return "\n".join([
            f"- **{service['name']}**: {service['description']} (Durata: {service['duration']} minute, Preț: {service['price']})"
            for service in self._info['services'].values()
        ])

    def get_dentists_text(self) -> str:
        """Get formatted dentists text."""
        return "\n".join([
            f"- **{dentist['name']}**: {dentist['specialty']} (experiență de {dentist['experience']}, {dentist['education']})"
            for dentist in self._info['dentists']
        ])

    def detect_symptoms(self, user_input: str) -> Dict:
        """
        Detect symptoms/needs from user input and suggest appropriate service.
        Returns dict with matched symptom type, service, priority, and message.
        """
        user_input_lower = user_input.lower()

        # Check each symptom category
        matches = []
        for symptom_type, symptom_data in self.symptom_mapping.items():
            for keyword in symptom_data["keywords"]:
                if keyword in user_input_lower:
                    matches.append({
                        "type": symptom_type,
                        "service": symptom_data["service"],
                        "priority": symptom_data["priority"],
                        "message": symptom_data["message"]
                    })
                    break  # Only count each symptom type once

        # Return highest priority match
        if matches:
            # Priority order: urgent > high > medium > low
            priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
            matches.sort(key=lambda x: priority_order.get(x["priority"], 99))
            return matches[0]

        return None

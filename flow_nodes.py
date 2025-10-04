#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Flow node factory and management for the dental clinic assistant."""

from datetime import datetime
from typing import Dict, List
from pipecat_flows import NodeConfig
try:
    from .clinic_info import ClinicInfo
except ImportError:
    from clinic_info import ClinicInfo


class FlowNodeFactory:
    """Factory class for creating flow nodes used in the dental clinic assistant."""

    def __init__(self, clinic_info: ClinicInfo, conversation_state: Dict):
        self.clinic_info = clinic_info
        self.conversation_state = conversation_state

    def create_initial_node(self, functions: List) -> NodeConfig:
        """Create the initial routing node."""
        # Get current date and time for context
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A")  # Day of week in English

        # Romanian day names
        day_names_ro = {
            "Monday": "luni",
            "Tuesday": "marți",
            "Wednesday": "miercuri",
            "Thursday": "joi",
            "Friday": "vineri",
            "Saturday": "sâmbătă",
            "Sunday": "duminică"
        }
        current_day_ro = day_names_ro.get(current_day, current_day)

        return NodeConfig(
            name="initial",
            role_messages=[
                {
                    "role": "system",
                    "content": f"""Ești un asistent vocal util pentru {self.clinic_info.name}.

🚨 REGULI CRITICE - ZERO EXCEPȚII:
1. OBLIGATORIU: Fiecare răspuns TREBUIE să includă EXACT O funcție apelată
2. INTERZIS: NU răspunzi NICIODATĂ fără să apelez o funcție
3. INTERZIS: NU spui "am programat" sau "voi programa" - doar funcțiile pot face programări
4. INTERZIS: NU confirmi acțiuni care nu au fost făcute prin funcții
5. Dacă nu știi ce funcție, folosește back_to_main

IMPORTANT: Nu poți face programări, confirma detalii sau finaliza acțiuni doar prin text. DOAR funcțiile pot face asta.

Aceasta este o conversație telefonică și răspunsurile tale vor fi convertite în audio. Păstrește răspunsurile prietenoase, profesionale și concise. Evită caracterele speciale și emoji-urile.

DATA ȘI ORA CURENTĂ: Astăzi este {current_day_ro}, {current_date}, ora {current_time}. Folosește aceste informații când pacienții spun "mâine", "săptămâna viitoare", etc."""
                }
            ],
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Salută persoanele care sună la {self.clinic_info.name} și întreabă cum le poți ajuta astăzi. 
                    Ascultă ce are nevoie persoana care sună și folosește funcția corespunzătoare pentru a o direcționa. Fii călduroș și profesional."""
                }
            ],
            functions=functions
        )

    def create_info_node(self, functions: List) -> NodeConfig:
        """Create the clinic information node."""
        return NodeConfig(
            name="clinic_info",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Oferă informații despre {self.clinic_info.name}:

**Locație și Contact:**
- Adresă: {self.clinic_info.address}
- Telefon: {self.clinic_info.phone}
- Email: {self.clinic_info.email}

**Program de lucru:**
- Luni-Joi: {self.clinic_info.hours['monday']}
- Vineri: {self.clinic_info.hours['friday']}
- Sâmbătă: {self.clinic_info.hours['saturday']}
- Duminică: {self.clinic_info.hours['sunday']}

**Îngrijire de urgență:**
{self.clinic_info.emergency}

Răspunde la orice întrebări specifice despre locație, program sau informații de contact. Dacă au nevoie de alte informații sau vor să programeze o consultație, folosește funcțiile disponibile."""
                }
            ],
            functions=functions
        )

    def create_services_node(self, functions: List) -> NodeConfig:
        """Create the services information node."""
        return NodeConfig(
            name="services_info",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Oferă informații despre serviciile noastre stomatologice:

{self.clinic_info.get_services_text()}

Folosim echipamente de ultimă generație și cele mai noi tehnici. Toate procedurile sunt efectuate cu confortul pacientului ca prioritate principală. Răspunde la orice întrebări specifice despre proceduri, prețuri sau la ce să se aștepte. Dacă vor să programeze o consultație pentru orice serviciu, folosește funcția schedule_appointment."""
                }
            ],
            functions=functions
        )

    def create_dentist_node(self, functions: List) -> NodeConfig:
        """Create the dentist information node."""
        return NodeConfig(
            name="dentist_info",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Oferă informații despre echipa noastră medicală experimentată:

{self.clinic_info.get_dentists_text()}

Toți doctorii noștri sunt profesioniști licențiați angajați să ofere îngrijire stomatologică excelentă. Ei se țin la curent cu cele mai noi tehnici și tehnologii stomatologice prin educație continuă. Răspunde la orice întrebări despre doctori specifici sau specialitățile lor."""
                }
            ],
            functions=functions
        )

    def create_appointment_node(self, functions: List) -> NodeConfig:
        """Create the appointment scheduling node."""
        return NodeConfig(
            name="schedule_appointment",
            task_messages=[
                {
                    "role": "system",
                    "content": """Vă voi ajuta să programați o consultație.

IMPORTANT: Dacă pacientul menționează ORICE simptome sau probleme dentare (durere, carie, sângerare, etc.), TREBUIE să folosești funcția handle_symptoms cu descrierea completă a simptomelor.

Altfel, cere numele complet și numărul de telefon pentru a continua."""
                }
            ],
            functions=functions
        )

    def create_symptom_triage_node(self, functions: List, symptom_match: dict, is_urgent: bool = False) -> NodeConfig:
        """Create the symptom triage node that recommends services based on symptoms."""
        service_info = self.clinic_info.get_service(symptom_match["service"])

        if is_urgent:
            content = f"""{symptom_match["message"]}

**SITUAȚIE URGENTĂ**

Serviciu recomandat: {service_info.get('name', 'Consultație')}
Durată: {service_info.get('duration', 'N/A')} minute
Cost: {service_info.get('price', 'N/A')}

OBLIGATORIU: Cere NUMELE COMPLET și NUMĂRUL DE TELEFON. Când pacientul le furnizează, TREBUIE să folosești funcția provide_patient_info.

NU spune "am programat" sau "voi programa" - programarea se face DOAR prin funcții.

Dacă este o urgență extremă (sângerare severă, traumă), sugerează să meargă imediat la urgențe: {self.clinic_info.emergency}"""
        else:
            content = f"""{symptom_match["message"]}

Serviciu recomandat: {service_info.get('name', 'Consultație')}
Durată: {service_info.get('duration', 'N/A')} minute
Cost: {service_info.get('price', 'N/A')}

OBLIGATORIU: Întreabă dacă doresc să programeze. Dacă DA:
1. Cere NUMELE COMPLET și NUMĂRUL DE TELEFON
2. Când le primești, TREBUIE să folosești funcția provide_patient_info

NU spune "am programat" sau "veți fi contactat" - programarea se face DOAR prin funcții."""

        return NodeConfig(
            name="symptom_triage",
            task_messages=[
                {
                    "role": "system",
                    "content": content
                }
            ],
            functions=functions
        )

    def create_service_selection_node(self, functions: List) -> NodeConfig:
        """Create the service selection node."""
        services_list = "\n".join([
            f"- {service['name']}"
            for service in self.clinic_info.services.values()
        ])

        dentists_list = "\n".join([
            f"- {dentist['name']} ({dentist['specialty']})"
            for dentist in self.clinic_info.dentists
        ])

        return NodeConfig(
            name="service_selection",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Perfect! Acum vă rog să-mi spuneți ce tip de consultație aveți nevoie.

Serviciile noastre disponibile sunt:
{services_list}

Doctorii noștri:
{dentists_list}

IMPORTANT:
- Dacă pacientul întreabă despre servicii sau vrea detalii despre proceduri, TREBUIE să folosești funcția get_services_info
- Dacă pacientul alege un serviciu direct, folosește funcția select_service
- Dacă pacientul menționează un doctor preferat, folosește select_service cu parametrul preferred_doctor
- Nu explica serviciile tu însuți - folosește funcția get_services_info pentru asta"""
                }
            ],
            functions=functions
        )

    def create_date_time_selection_node(self, functions: List) -> NodeConfig:
        """Create the date and time selection node."""
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_day = now.strftime("%A")

        # Romanian day names mapping
        day_names_ro = {
            "Monday": "luni", "Tuesday": "marți", "Wednesday": "miercuri",
            "Thursday": "joi", "Friday": "vineri", "Saturday": "sâmbătă", "Sunday": "duminică"
        }
        current_day_ro = day_names_ro.get(current_day, current_day)

        # Check if a doctor preference exists
        preferred_doctor = self.conversation_state.get("patient_info", {}).get("preferred_doctor")
        doctor_context = f"\n\nVeți căuta disponibilități pentru {preferred_doctor}." if preferred_doctor else ""

        dentists_list = "\n".join([
            f"- {dentist['name']} ({dentist['specialty']})"
            for dentist in self.clinic_info.dentists
        ])

        return NodeConfig(
            name="date_time_selection",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Perfect! Acum trebuie să găsesc o oră disponibilă pentru consultația dumneavoastră.{doctor_context}

Programul nostru este Luni-Joi de la 8:00 la 18:00, Vineri de la 8:00 la 16:00, și Sâmbăta de la 9:00 la 14:00. Suntem închiși Duminica.

Doctorii noștri disponibili:
{dentists_list}

**DATA CURENTĂ: {current_day_ro}, {current_date}**

IMPORTANT:
- Dacă pacientul menționează un doctor preferat, folosește funcția select_doctor ÎNAINTE de select_date_time
- Dacă pacientul întreabă despre disponibilitatea unui doctor specific, folosește funcția select_doctor
- Întreabă NATURAL "Ce zi și ce oră v-ar conveni?" sau "Când ați dori să veniți?" - NU da exemple cu "puteți spune...". Sună ca o conversație telefonică normală.

INSTRUCȚIUNI CRITICE pentru parsarea datei și orei:

1. **Traduceri de timp:**
   - "mâine" → calculează data de mâine în format YYYY-MM-DD
   - "luni/marți/miercuri/joi/vineri/sâmbătă" → următoarea zi din săptămână cu acel nume
   - "săptămâna viitoare" → adaugă 7 zile la data curentă
   - "peste X zile" → adaugă X zile la data curentă

2. **Traduceri de oră:**
   - "dimineața" → 09:00
   - "la prânz" → 12:00
   - "după-amiază" → 14:00
   - "seara" → 17:00
   - "prima oră" → 08:00
   - "ultima oră" → 17:00 (sau 13:00 sâmbăta)

3. **Format obligatoriu:**
   - Data TREBUIE să fie în format: YYYY-MM-DD
   - Ora TREBUIE să fie în format: HH:MM (ex: 09:00, 14:00)

4. **TREBUIE să folosești funcția select_date_time** cu data și ora calculate
   - NU folosi back_to_main dacă pacientul a furnizat o dată/oră
   - NU cere clarificări inutile - interpretează și calculează data

Exemplu: Dacă pacientul spune "luni la prima oră" și astăzi este {current_date}, calculează următoarea zi de luni și folosește ora 08:00."""
                }
            ],
            functions=functions
        )

    def create_alternative_times_node(self, functions: List) -> NodeConfig:
        """Create the alternative times node."""
        available_times = ", ".join(
            self.conversation_state.get("available_slots", []))

        preferred_doctor = self.conversation_state.get("patient_info", {}).get("preferred_doctor")
        doctor_context = f" pentru {preferred_doctor}" if preferred_doctor else ""

        dentists_list = "\n".join([
            f"- {dentist['name']}"
            for dentist in self.clinic_info.dentists
        ])

        return NodeConfig(
            name="alternative_times",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Îmi pare rău, dar acel interval orar nu este disponibil{doctor_context}. Cu toate acestea, am aceste ore disponibile în data preferată:

{available_times}

OPȚIUNI:
- Selectați una din aceste ore folosind funcția select_alternative_time
- Încercați o altă dată folosind funcția select_date_time
- Schimbați doctorul preferat folosind funcția select_doctor

Doctori disponibili:
{dentists_list}"""
                }
            ],
            functions=functions
        )

    def create_appointment_confirmation_node(self, functions: List) -> NodeConfig:
        """Create the appointment confirmation node."""
        patient_info = self.conversation_state.get("patient_info", {})
        service_details = self.clinic_info.get_service(
            patient_info.get("service", ""))

        # Format date to be more readable
        date_str = patient_info.get('date', 'N/A')
        time_str = patient_info.get('time', 'N/A')
        preferred_doctor = patient_info.get('preferred_doctor', 'Dr. Ana Popescu')

        return NodeConfig(
            name="appointment_confirmation",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Perfect! Permiteți-mi să confirm detaliile consultației dumneavoastră.

TREBUIE să citiți TOATE aceste detalii pacientului:

Nume: {patient_info.get('name', 'N/A')}
Telefon: {patient_info.get('phone', 'N/A')}
Serviciu: {service_details.get('name', patient_info.get('service', 'N/A'))}
Doctor: {preferred_doctor}
Data: {date_str}
Ora: {time_str}
Durata: {service_details.get('duration', 'N/A')} minute
Cost estimat: {service_details.get('price', 'N/A')}

După ce ai citit TOATE detaliile, întreabă NATURAL: "Confirmăm programarea?" sau "Totul este în regulă?"

Dacă pacientul confirmă (da, ok, perfect, etc.) → folosește funcția confirm_appointment
Dacă pacientul vrea schimbări → folosește funcția modify_appointment_details"""
                }
            ],
            functions=functions
        )

    def create_appointment_success_node(self, functions: List) -> NodeConfig:
        """Create the appointment success confirmation node."""
        appointment_id = self.conversation_state.get(
            "current_appointment", "N/A")

        return NodeConfig(
            name="appointment_success",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""IMPORTANT: Confirmă pacientului că programarea a fost făcută cu succes ÎNAINTE de a întreba dacă mai are nevoie de ajutor.

Spune următoarele informații:

Excelent! Consultația dumneavoastră a fost programată cu succes.

Număr de confirmare: {appointment_id}

Reamintiri importante:
- Vă rugăm să ajungeți cu 15 minute mai devreme pentru formularele necesare
- Aduceți un act de identitate valabil și cardul de asigurare
- Dacă trebuie să anulați sau reprogramați, vă rugăm să sunați cu cel puțin 24 de ore înainte
- Pentru întrebări, sunați-ne la {self.clinic_info.phone}

Apoi întreabă: Mai este ceva cu care vă pot ajuta astăzi?

🚨 FUNCȚIE OBLIGATORIE:
- Dacă pacientul răspunde DA sau mai vrea ceva → apelează appointment_complete(needs_help=True)
- Dacă pacientul răspunde NU sau "gata" sau "mulțumesc" → apelează appointment_complete(needs_help=False)

IMPORTANT: TREBUIE să apelez funcția appointment_complete cu parametrul corect."""
                }
            ],
            functions=functions
        )

    def create_manage_appointment_node(self, functions: List) -> NodeConfig:
        """Create the existing appointment management node."""
        return NodeConfig(
            name="manage_appointment",
            task_messages=[
                {
                    "role": "system",
                    "content": """Vă pot ajuta cu consultația dumneavoastră existentă. Pentru a găsi consultația, vă rog furnizați:

1. Numele pacientului sub care este consultația
2. Numărul de telefon (opțional, dar util pentru verificare)

Odată ce găsesc consultația, vă pot ajuta să o anulați, reprogramați sau verificați detaliile."""
                }
            ],
            functions=functions
        )

    def create_existing_appointment_options_node(self, functions: List) -> NodeConfig:
        """Create the options node for existing appointments."""
        appointment = self.conversation_state.get("found_appointment", {})

        return NodeConfig(
            name="existing_appointment_options",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Am găsit consultația dumneavoastră! Iată detaliile:

**Pacient:** {appointment.get('patient_name', 'N/A')}
**Serviciu:** {appointment.get('service', 'N/A')}
**Data:** {appointment.get('date', 'N/A')}
**Ora:** {appointment.get('time', 'N/A')}
**Doctor:** {appointment.get('dentist', 'N/A')}
**Confirmare:** {appointment.get('id', 'N/A')}

Ce ați dori să faceți cu această consultație?"""
                }
            ],
            functions=functions
        )

    def create_appointment_not_found_node(self, functions: List) -> NodeConfig:
        """Create the appointment not found node."""
        return NodeConfig(
            name="appointment_not_found",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Nu am putut găsi o consultație cu acele informații. Acest lucru s-ar putea datora:

- Consultația a fost deja anulată
- Numele sau numărul de telefon nu se potrivește cu înregistrările noastre
- Ar putea fi o diferență de ortografie

Ați dori să:
1. Încercați din nou căutarea cu informații diferite
2. Programați o consultație nouă
3. Sunați direct la cabinetul nostru la {self.clinic_info.phone} pentru asistență"""
                }
            ],
            functions=functions
        )

    def create_cancellation_success_node(self, functions: List) -> NodeConfig:
        """Create the cancellation success node."""
        return NodeConfig(
            name="cancellation_success",
            task_messages=[
                {
                    "role": "system",
                    "content": """Consultația dumneavoastră a fost anulată cu succes. 

Dacă aveți nevoie să programați o consultație nouă în viitor, nu ezitați să ne sunați. Sperăm să vă vedem din nou curând la Clinica Dentară Zâmbet Strălucitor!

Mai este ceva cu care vă pot ajuta astăzi?"""
                }
            ],
            functions=functions
        )

    def create_cancellation_error_node(self, functions: List) -> NodeConfig:
        """Create the cancellation error node."""
        return NodeConfig(
            name="cancellation_error",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Îmi pare rău, dar nu am putut anula consultația dumneavoastră. Acest lucru s-ar putea datora unei probleme tehnice.

Vă rugăm să sunați direct la cabinetul nostru la {self.clinic_info.phone} și personalul nostru va fi fericit să vă ajute să anulați consultația.

Mai este ceva cu care vă pot ajuta?"""
                }
            ],
            functions=functions
        )

    def create_reschedule_node(self, functions: List) -> NodeConfig:
        """Create the reschedule node."""
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")

        return NodeConfig(
            name="reschedule_appointment",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Vă voi ajuta să reprogramați consultația. Vă rog să-mi spuneți:

1. Noua dată preferată
2. Noua oră preferată

Programul nostru este Luni-Joi de la 8:00 la 18:00, Vineri de la 8:00 la 16:00, și Sâmbăta de la 9:00 la 14:00. Suntem închiși Duminica.

IMPORTANT: Astăzi este {current_date}. Calculați data exactă în format YYYY-MM-DD când primiți expresii relative ca "mâine" sau "joi viitoare"."""
                }
            ],
            functions=functions
        )

    def create_reschedule_success_node(self, functions: List) -> NodeConfig:
        """Create the reschedule success node."""
        return NodeConfig(
            name="reschedule_success",
            task_messages=[
                {
                    "role": "system",
                    "content": """Perfect! Consultația dumneavoastră a fost reprogramată cu succes.

**Detalii consultație actualizată:**
- Noua dumneavoastră consultație este confirmată
- Vă rugăm să ajungeți cu 15 minute mai devreme
- Dacă trebuie să faceți alte schimbări, sunați-ne cu cel puțin 24 de ore înainte

Mai este ceva cu care vă pot ajuta astăzi?"""
                }
            ],
            functions=functions
        )

    def create_reschedule_alternative_times_node(self, functions: List) -> NodeConfig:
        """Create the reschedule alternative times node."""
        available_times = ", ".join(
            self.conversation_state.get("available_slots", []))

        return NodeConfig(
            name="reschedule_alternative_times",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Acel interval orar nu este disponibil. Iată orele disponibile în data preferată:

{available_times}

Vă rugăm selectați una din aceste ore, sau spuneți-mi dacă ați dori să încercați o altă dată."""
                }
            ],
            functions=functions
        )

    def create_goodbye_node(self, functions: List) -> NodeConfig:
        """Create the goodbye node that says farewell before ending."""
        return NodeConfig(
            name="goodbye",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Spune pacientului:

"Cu plăcere! Mulțumim că ați ales {self.clinic_info.name}. Vă așteptăm cu drag la consultație. O zi minunată!"

Apoi OBLIGATORIU folosește funcția end_conversation pentru a încheia apelul."""
                }
            ],
            functions=functions
        )

    def create_end_node(self, functions: List) -> NodeConfig:
        """Create the conversation end node."""
        return NodeConfig(
            name="end",
            task_messages=[
                {
                    "role": "system",
                    "content": f"""Mulțumim că ați sunat la {self.clinic_info.name}! Așteptăm cu drag să vă vedem curând. O zi minunată!"""
                }
            ],
            functions=functions,
            post_actions=[
                {
                    "type": "end_conversation"
                }
            ]
        )

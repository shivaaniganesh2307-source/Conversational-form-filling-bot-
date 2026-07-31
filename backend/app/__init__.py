{
  "MEDICAL_FORM": [
    {
      "id": "first_name",
      "label": "First name",
      "type": "name",
      "required": True
    },
    {
      "id": "last_name",
      "label": "Last name",
      "type": "name",
      "required": True
    },
    {
      "id": "date_of_birth",
      "label": "Date of birth",
      "type": "date",
      "required": True
    },
    {
      "id": "gender",
      "label": "Gender",
      "type": "toggle",
      "options": ["Male", "Female"],
      "condition": {
        "id": "pregnant",
        "label": "Are you pregnant?",
        "type": "toggle",
        "options": ["Yes", "No"],
        "required": True
      }
    },
    {
      "id": "address",
      "label": "Address",
      "type": "address",
      "required": True
    },
    {
      "id": "phone_number",
      "label": "Phone number",
      "type": "text",
      "validation": "phone",
      "required": True
    },
    {
      "id": "email",
      "label": "Email",
      "type": "text",
      "validation": "email",
      "required": True
    },
    {
      "id": "medical_history",
      "label": "Medical history",
      "type": "textarea",
      "required": False
    },
    {
      "id": "current_medications",
      "label": "Current medications",
      "type": "textarea",
      "required": False
    },
    {
      "id": "allergies",
      "label": "Allergies",
      "type": "textarea",
      "required": False,
      "condition":[{
      "id": "emergency_contact_name",
      "label": "Emergency contact name",
      "type": "name",
      "required": True
     },
     {
      "id": "emergency_contact_relationship",
      "label": "Emergency contact relationship",
      "type": "text",
      "required": True
     }
     ]},
    {
      "id": "emergency_contact_name",
      "label": "Emergency contact name",
      "type": "name",
      "required": True
    },
    {
      "id": "emergency_contact_relationship",
      "label": "Emergency contact relationship",
      "type": "text",
      "required": True
    }

  ],
  "OSHA_FORM": [
    {
      "id": "first_name",
      "label": "First name",
      "type": "name",
      "required": True
    },
    {
      "id": "middle_name",
      "label": "Middle name",
      "type": "name",
      "required": True
    },
    {
      "id": "last_name",
      "label": "Last name",
      "type": "name",
      "required": True
    },
    {
      "id": "uic",
      "label": "UIC",
      "type": "text",
      "validation": "alphanumeric",
      "required": True
    },
    {
      "id": "street_name",
      "label": "Street",
      "type": "address",
      "required": True
    },
    {
      "id": "city",
      "label": "City",
      "type": "address",
      "required": True
    },
    {
      "id": "state",
      "label": "State",
      "type": "address",
      "required": True
    },
    {
      "id": "zipcode",
      "label": "Zipcode",
      "type": "address",
      "required": True
    },
    {
      "id": "date_of_birth",
      "label": "Date of birth",
      "type": "date",
      "required": True
    },
    {
      "id": "date_hired",
      "label": "Date hired",
      "type": "date",
      "required": True
    },
    {
      "id": "date_of_injury_illness",
      "label": "Date of injury/illness",
      "type": "date",
      "required": True
    },
    {
      "id": "time_employee_started_work",
      "label": "Time employee started work",
      "type": "time",
      "required": False
    },
    {
      "id": "time_of_event",
      "label": "Time of event",
      "type": "time",
      "required": False
    },
    {
      "id": "before_incident",
      "label": "Before incident",
      "type": "textarea",
      "required": True
    },
    {
      "id": "what_happened",
      "label": "What happened",
      "type": "textarea",
      "required": True
    },
    {
      "id": "gender",
      "label": "Gender",
      "type": "toggle",
      "options": ["Male", "Female"],
      "required": False
    },
    {
      "id": "name_of_physician",
      "label": "Name of physician",
      "type": "name",
      "required": True
    },
    {
      "id": "facility",
      "label": "Facility",
      "type": "name",
      "required": False
    },
    {
      "id": "faculty_street",
      "label": "Faculty street",
      "type": "address",
      "required": False
    },
    {
      "id": "faculty_city",
      "label": "Faculty city",
      "type": "address",
      "required": False
    },
    {
      "id": "faculty_state",
      "label": "Faculty state",
      "type": "address",
      "required": False
    },
    {
      "id": "faculty_zipcode",
      "label": "Faculty zipcode",
      "type": "address",
      "required": False
    },
    {
      "id": "employee_treated_emergency_room",
      "label": "Employee treated in emergency room",
      "type": "toggle",
      "options": ["Yes", "No"],
      "required": True
    },
    {
      "id": "employee_hospitalized_overnight",
      "label": "Employee hospitalized overnight",
      "type": "toggle",
      "options": ["Yes", "No"],
      "required": True
    }
  ]
}

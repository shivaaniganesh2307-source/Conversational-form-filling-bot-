#say the message to the user 
# Creates chatbot responses based on the action decided by the system
class ResponseGenerator:
    
    def generate(self, action_plan, schema):
        action = action_plan.get("action") #get what action needs to happen
        #get the field that the action is related to 
        target_field = action_plan.get("field")
        field_label = target_field
        if target_field in schema.get("fields", {}):
            field_label = schema["fields"][target_field].get("label",target_field)
        #handle validation errors 
        if action == "CORRECT_VALIDATION_ERROR":
            messages = action_plan.get("messages",[])
            error_message = " ".join(messages)
            return (
                f"There is an issue with your "
                f"{field_label}: {error_message}"
            )
        if action == "CONFIRM_LOW_CONFIDENCE":
            value = action_plan.get(
                "unconfirmed_value"
            )
            return (
                f"Did you mean your {field_label} "
                f"is '{value}'?"
                " Please confirm or re-enter."
            )
        if action == "REQUEST_MISSING_FIELD":
            return f"Please provide your {field_label}."
        if action == "COMPLETE_FORM":
            return (
                "Thank you! "
                "All required form details have been collected and saved."
            )
        return "How can I help you complete your form?"





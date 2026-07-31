
class Planner:
    def next_question(self,validation_errors,missing_fields,low_confidence_fields):
        #sending planner to response generator for Validation error
        if validation_errors:
            for field_name in validation_errors:
                return {
                    "action": "CORRECT_VALIDATION_ERROR",
                    "field":field_name,
                    "messages":validation_errors[field_name]
                }
        #sending planner to response generator for missing fields       
        if missing_fields:
           for field_name in missing_fields:
                return{
                    "action":"GET_MISSING_FIELDS",
                    "field":field_name
                }
        #sending planner to response generator for low confidence fields 
        if low_confidence_fields: 
            for field_name in low_confidence_fields:
                return{
                    "action":"GET_MISSING_FIELDS",
                    "field":field_name,
                    "unconfirmed": "" 
                }
        #final message :)
        return{"action":"compete_form"}           


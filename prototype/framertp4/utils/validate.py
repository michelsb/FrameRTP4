required_fields = set(["match_fields","action_name","action_params","priority"])

def validate_rule_fields(rule):
    rule_fields = set(rule.keys())
    missing_fields = required_fields - rule_fields
    if len(missing_fields) > 0:
        message = "Missing fields: " + str(missing_fields)
        return False, message
    strange_fields = rule_fields - required_fields
    if len(strange_fields) > 0:
        message = "Too much fields: " + str(strange_fields)
        return False, message
    return True, "OK!"

# def validate_rule_match_fields(rule_match_fields, required_match_fields):
#     rule_match_fields = set(rule_match_fields)
#     required_match_fields = set(required_match_fields)
#     missing_match_fields = required_match_fields - rule_match_fields
#     if len(missing_match_fields) > 0:
#         message = "missing match fields: " + str(missing_match_fields)
#         return false, message
#     strange_match_fields = rule_match_fields - required_match_fields
#     if len(strange_match_fields) > 0:
#         message = "too much match fields: " + str(strange_match_fields)
#         return false, message
#     return true, "ok!"

def validate_rule_match_fields(rule, keys):
    required_match_fields = set([key["name"] for key in keys])
    rule_match_fields = set(rule["match_fields"].keys())
    required_match_fields = set(required_match_fields)
    missing_match_fields = required_match_fields - rule_match_fields
    if len(missing_match_fields) > 0:
        message = "Missing match fields: " + str(missing_match_fields)
        return False, message
    strange_match_fields = rule_match_fields - required_match_fields
    if len(strange_match_fields) > 0:
        message = "Too much match fields: " + str(strange_match_fields)
        return False, message
    for key in keys:
        value = rule["match_fields"][key["name"]]
        match_type = key["match_type"]
        size = key["size"]
        if match_type == "lpm":
            if not isinstance(value, list):
                message = "LPM fields must receive a list with two arguments: [value, mask]!"
                return False, message
            if not isinstance(value[1], int):
                message = "The second argument in LPM fields must be integer type!"
                return False, message
            if value[1] > size:
                message = "The mask value '%s' in LPM fields cannot be greater than field size '%s'!" % (str(value[1]),str(size))
                return False, message
        # if (match_type == "ternary") or (match_type == "lpm"):
        #     if not isinstance(value, list):
        #         message = "Ternary and LPM fields must receive a list with two arguments: [value, mask]!"
        #         return False, message
        #     #if not isinstance(value[0], unicode):
        #     #    message = "The first argument in Ternary and LPM fields must be string type!"
        #     #    return False, message
        #     if not isinstance(value[1], int):
        #         message = "The second argument in Ternary and LPM fields must be integer type!"
        #         return False, message
        #     if value[1] > size:
        #         message = "The mask value '%s' in Ternary and LPM fields cannot be greater than field size '%s'!" % (str(value[1]),str(size))
        #         return False, message
        #else:
            #if not isinstance(value, unicode):
                #message = "All '%s' field must be string type!" % match_type
                #return False, message

    return True, "OK!"

#def validate_rule_action(rule_action, allowed_actions):
#    if rule_action not in allowed_actions:
#        message = "The following action is not available for this P4Table: " + str(rule_action)
#        return False, message
#    return True, "OK!"

def validate_rule_action(rule, actions):
    rule_action_name = rule["action_name"]
    if not isinstance(rule_action_name, str):
        message = "The action_name field must by string type!"
        return False, message
    selected_action = None
    for action in actions:
        if rule_action_name == action["name"]:
            selected_action = action
    if selected_action is None:
        message = "The following action is not available for this P4Table: " + str(rule_action_name)
        return False, message
    if len(rule["action_params"]) > 0:
        rule_action_params = set(rule["action_params"].keys())
    else:
        rule_action_params = set()
    if len(list(selected_action["runtime_data"])) > 0:
        required_action_params = set([e["name"] for e in selected_action["runtime_data"]])
        missing_action_params = required_action_params - rule_action_params
        if len(missing_action_params) > 0:
            message = "Missing action parameters: " + str(missing_action_params)
            return False, message
        strange_action_params = rule_action_params - required_action_params
        if len(strange_action_params) > 0:
            message = "Too much action parameters: " + str(strange_action_params)
            return False, message
    return True, "OK!"

def validate_rule_priority(rule):
    priority = rule["priority"]
    if not isinstance(priority, int):
        message = "The priority field must be integer type!"
        return False, message
    return True, "OK!"

def validate_rule(submitted_rule, p4table):
    ## Rule Fields
    response, message = validate_rule_fields(submitted_rule)
    if not response:
        return response, message
    ## Match Fields
    #required_match_fields = [key["name"] for key in p4table["keys"]]
    #response, message = validate_rule_match_fields(submitted_rule["match_fields"].keys(), required_match_fields)
    response, message = validate_rule_match_fields(submitted_rule, p4table["keys"])
    if not response:
        return response, message
    ## Action
    response, message = validate_rule_action(submitted_rule, p4table["actions"])
    if not response:
        return response, message
    ## Priority
    response, message = validate_rule_priority(submitted_rule)
    if not response:
        return response, message
    return True, "Valid rule!"
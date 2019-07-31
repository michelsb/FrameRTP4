class UIn_Error(Exception):
    def __init__(self, info=""):
        self.info = info
    def __str__(self):
        return self.info

class UIn_ResourceError(UIn_Error):
    def __init__(self, res_type, name):
        self.res_type = res_type
        self.name = name
    def __str__(self):
        return "Invalid %s name (%s)" % (self.res_type, self.name)

class UIn_Error(Exception):
    def __init__(self, info=""):
        self.info = info
    def __str__(self):
        return self.info
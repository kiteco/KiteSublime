class ExpectedError(Exception):
    """Raised when an expected error happens.
    """
    def __init__(self, exc, message):
        self.exc = exc
        self.message = message

class MultipleSelectionError(ExpectedError):
    pass

class EmptyLineSelectionError(ExpectedError):
    pass

class PathNotInSupportedProjectError(ExpectedError):
    pass

class ProjectStillIndexingError(ExpectedError):
    pass

class GenericRelatedCodeError(ExpectedError):
    pass

from enum import Enum

class ConflictResolutionStrategy(str, Enum):
    PROMPT = "prompt"
    MERGE = "merge"
    KEEP_SEPARATE = "keep_separate"
    SKIP = "skip"
    DELETE = "delete"
    EDIT = "edit"

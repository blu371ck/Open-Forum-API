import enum


class UserRole(enum.Enum):
    USER = "User"
    MANAGER = "Manager"
    EXECUTIVE = "Executive"
    DEVELOPER = "Developer"


class Region(enum.Enum):
    EAST = "East"
    WEST = "West"
    NORTH = "North"
    SOUTH = "South"


class Site(enum.Enum):
    NEW_YORK = "New York, NY"
    MINNEAPOLIS = "Minneapolis, MN"
    DALLAS = "Dallas, TX"
    SEATTLE = "Seattle, WA"


class WalkStatus(enum.Enum):
    CREATED = "Created"
    IN_PROGRESS = "In-Progress"
    COMPLETED = "Completed"


class FeedbackStatus(enum.Enum):
    CREATED = "create"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In-Progress"
    SUCCESSFUL = "Successful"
    UNSUCCESSFUL = "Unsuccessful"


class TagType(enum.Enum):
    GLOBAL = "Global"
    REGIONAL = "Regional"
    SITE_SPECIFIC = "Site-Specific"
    IMPACTFUL = "Impactful"
    PROFILE_SPECIFIC = "Profile-Specific"

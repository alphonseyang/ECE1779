# constants for the User table index
USERNAME = 0
PASSWORD = 1
ROLE = 2


# constants for role types
ADMIN = "admin"
USER = "user"

# constants for photo categories
NO_FACES_DETECTED = 0
ALL_FACES_WEAR_MASKS = 1
NO_FACES_WEAR_MASKS = 2
PARTIAL_FACES_WEAR_MASKS = 3


# constants for detection file location
# the path is relative to the venv/bin/
DEST_FOLDER = "images/"
TEMP_FOLDER = "images/temp/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

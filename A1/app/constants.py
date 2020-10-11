# constants for the User table index
USERNAME = 0
PASSWORD = 1
ROLE = 2
SECURITY_ANSWER = 3
MODIFIED_ANSWER = 4


# constants for role types
ADMIN = "admin"
USER = "user"
RESERVED_NAMES = {"temp", "test", "root"}
TEN_MB = 1048576

# constants for photo categories
NO_FACES_DETECTED = 0
ALL_FACES_WEAR_MASKS = 1
NO_FACES_WEAR_MASKS = 2
PARTIAL_FACES_WEAR_MASKS = 3
CATEGORY_MAP = {
    NO_FACES_DETECTED: "No face detected in image",
    ALL_FACES_WEAR_MASKS: "All faces from image are wearing masks",
    NO_FACES_WEAR_MASKS: "No face from image is wearing masks",
    PARTIAL_FACES_WEAR_MASKS: "Only some faces from image are wearing masks"
}


# constants for detection file location
# the path is relative to the A1/
STATIC_PREFIX = "app/static/"
DEST_FOLDER = "images/"
TEMP_FOLDER = "app/static/images/temp/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

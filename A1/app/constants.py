# constants for the User table index
USERNAME = 0
PASSWORD = 1
ROLE = 2
SECURITY_ANSWER = 3
MODIFIED_ANSWER = 4

# constants related to flashed message type
ERROR = "error"
INFO = "info"

# constants for role types
ADMIN = "admin"
USER = "user"

# constants for image validation
TEN_MB = 1048576
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

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
USER_FOLDER = "app/static/images/{}"
PROCESSED_FOLDER = "app/static/images/{}/processed/"
UNPROCESSED_FOLDER = "app/static/images/{}/unprocessed/"
THUMBNAIL_FOLDER = "app/static/images/{}/thumbnail/"

# constants for user creation
RESERVED_NAMES = {"temp", "test", "root"}

# constants for S3 bucket
BUCKET_NAME = "ece1779yangkuangwang-bucket"

# constants used to control local or AWS storage
IS_REMOTE = True

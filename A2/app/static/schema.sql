USE ECE1779;

DROP TABLE image;
DROP TABLE user;

CREATE TABLE user (
    username varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    role varchar(255) NOT NULL,
    security_answer varchar(255) NOT NULL,
    modified_answer BOOLEAN NOT NULL default FALSE,
    PRIMARY KEY (username)
)ENGINE=InnoDB;

INSERT INTO user (username, password, role,security_answer) VALUES ("root", "*****", "admin","*****");

CREATE TABLE image (
    image_id varchar(255) NOT NULL,
    processed_image_path varchar(255) NOT NULL,
    unprocessed_image_path varchar(255) NOT NULL,
    thumbnail_image_path varchar(255) NOT NULL,
    category int NOT NULL,
    num_faces int NOT NULL,
    num_masked int NOT NULL,
    num_unmasked int NOT NULL,
    username varchar(255) NOT NULL,
    created_at timestamp default current_timestamp,
    PRIMARY KEY (image_id),
    FOREIGN KEY (username) REFERENCES user(username)
    ON DELETE CASCADE
)ENGINE=InnoDB;
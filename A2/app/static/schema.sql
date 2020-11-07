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

INSERT INTO user (username, password, role,security_answer) VALUES ("root", "196cf6904772a8b6d7567a0b7cb041eba0e260fb3497971eddd5c4d7eb68fc1a315aa827d99bba01d02c6373445066cc186c5b7c095396906bd5c204d5a902720b07687e4e7698d0574e80dd7d823f8506c22aafbf2bb4c59cd54787459ebc62", "admin","63eca2b3bcee0afc762cd949e6f6eb2e855e86a5225bce44a3efb0615558461e1e2ef472441c29cbc81b6bec404e7b7ee8b2145387f764449fedd7001e054422791b060b82cf92218fcf0369b99548106eb3c93188dee017e417c17c689277cd");

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
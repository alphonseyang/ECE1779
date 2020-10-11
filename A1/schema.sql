DROP DATABASE IF EXISTS ECE1779A1;
CREATE DATABASE ECE1779A1;
USE ECE1779A1;

CREATE TABLE user (
    username varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    role varchar(255) NOT NULL,
    security_answer varchar(255) default 'default',
    modified_answer int NOT NULL default 0,
    PRIMARY KEY (username)
)ENGINE=InnoDB;

-- create initial admin/user users to start
INSERT INTO user (username, password, role) VALUES ("root", "root", "admin");
INSERT INTO user (username, password, role) VALUES ("user1", "user1", "user");

CREATE TABLE image (
    image_id varchar(255) NOT NULL,
    image_path varchar(255) NOT NULL,
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

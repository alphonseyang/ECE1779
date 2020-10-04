DROP DATABASE IF EXISTS ECE1779A1;
CREATE DATABASE ECE1779A1;
USE ECE1779A1;

CREATE TABLE user (
    username varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    role varchar(255) NOT NULL,
    PRIMARY KEY (username)
);

-- create initial admin/user users to start
INSERT INTO user (username, password, role) VALUES ("root", "root", "admin");
INSERT INTO user (username, password, role) VALUES ("user1", "user1", "user");

CREATE TABLE photo (
    photo_id int NOT NULL AUTO_INCREMENT,
    photo_path varchar(255) NOT NULL,
    category int NOT NULL,
    username varchar(255) NOT NULL,
    created_at timestamp default current_timestamp,
    PRIMARY KEY (photo_id),
    FOREIGN KEY (username) REFERENCES user(username)
);
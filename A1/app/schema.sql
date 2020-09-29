DROP DATABASE IF EXISTS ECE1779A1;
CREATE DATABASE ECE1779A1;
USE ECE1779A1;

CREATE TABLE user (
    username varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    role varchar(255) NOT NULL,
    PRIMARY KEY (username)
);

-- create an initial admin user to start
INSERT INTO user (username, password, role) VALUES ("root", "root", "admin");
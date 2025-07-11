-- Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS mydb;

-- Switch to using the 'mydb' database
USE mydb;

-- Create the 'students' table if it doesn't already exist
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each student, auto-increments
    name VARCHAR(100) NOT NULL,         -- Student's name, cannot be empty, max 100 characters
    age INT NOT NULL                    -- Student's age, cannot be empty
);

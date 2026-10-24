CREATE DATABASE IF NOT EXISTS blood_bank_db;
USE blood_bank_db;
CREATE TABLE IF NOT EXISTS users(user_id INT AUTO_INCREMENT PRIMARY KEY,username VARCHAR(50) UNIQUE NOT NULL,user_password VARCHAR(255) NOT NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS persons(person_id INT AUTO_INCREMENT PRIMARY KEY,name VARCHAR(100) NOT NULL,address VARCHAR(255),phone VARCHAR(20),blood_group ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,gender ENUM('Male','Female','Other') NOT NULL,date_of_birth DATE,medical_issues VARCHAR(255)) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS donations(donation_id INT AUTO_INCREMENT PRIMARY KEY,person_id INT NOT NULL,donation_date DATE NOT NULL,donation_time TIME NOT NULL,quantity_ml INT NOT NULL CHECK(quantity_ml>0),FOREIGN KEY(person_id) REFERENCES persons(person_id)) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS receives(receive_id INT AUTO_INCREMENT PRIMARY KEY,person_id INT NOT NULL,hospital VARCHAR(150) NOT NULL,receive_date DATE NOT NULL,blood_group ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,quantity_ml INT NOT NULL CHECK(quantity_ml>0),status ENUM('Approved','Pending') NOT NULL DEFAULT 'Pending',FOREIGN KEY(person_id) REFERENCES persons(person_id)) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS blood_stock(blood_group ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') PRIMARY KEY,quantity_ml INT NOT NULL DEFAULT 0 CHECK(quantity_ml>=0)) ENGINE=InnoDB;
INSERT IGNORE INTO blood_stock VALUES('A+',0),('A-',0),('B+',0),('B-',0),('AB+',0),('AB-',0),('O+',0),('O-',0);

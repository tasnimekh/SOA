CREATE DATABASE IF NOT EXISTS entreprise_db CHARACTER SET utf8mb4;
USE entreprise_db;

CREATE TABLE entreprise (
  id_entreprise INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(150) NOT NULL, pays VARCHAR(80) NOT NULL, secteur VARCHAR(100) NOT NULL
);

CREATE TABLE encadrant_pro (
  id_encadrant_pro INT AUTO_INCREMENT PRIMARY KEY,
  id_entreprise INT NOT NULL,
  nom VARCHAR(100) NOT NULL, email VARCHAR(150) NOT NULL, poste VARCHAR(100) NOT NULL,
  CONSTRAINT fk_encpro_entreprise FOREIGN KEY (id_entreprise) REFERENCES entreprise(id_entreprise)
);

CREATE TABLE convention (
  id_convention INT AUTO_INCREMENT PRIMARY KEY,
  id_stage INT NOT NULL UNIQUE,              -- reference vers le Stage Service (pas de FK entre bases)
  id_entreprise INT NOT NULL,
  id_encadrant_pro INT NOT NULL,
  type_stage VARCHAR(10) NOT NULL,           -- local | etranger
  pays VARCHAR(80) NOT NULL,
  statut VARCHAR(15) NOT NULL DEFAULT 'en_attente',  -- en_attente | signee | terminee
  CONSTRAINT fk_conv_entreprise FOREIGN KEY (id_entreprise) REFERENCES entreprise(id_entreprise),
  CONSTRAINT fk_conv_encpro FOREIGN KEY (id_encadrant_pro) REFERENCES encadrant_pro(id_encadrant_pro)
);

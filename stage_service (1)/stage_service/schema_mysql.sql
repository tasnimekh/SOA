CREATE DATABASE IF NOT EXISTS stage_db CHARACTER SET utf8mb4;
USE stage_db;

-- Hierarchie 1 : etudiant (mere) <- stagiaire (fille, meme identifiant)
CREATE TABLE etudiant (
  id_etudiant INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL, prenom VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL, classe VARCHAR(50) NOT NULL,
  type VARCHAR(20) NOT NULL DEFAULT 'etudiant'          -- etudiant | stagiaire
);
CREATE TABLE stagiaire (
  id_etudiant INT PRIMARY KEY,
  date_statut DATE NOT NULL,
  CONSTRAINT fk_stagiaire_etudiant FOREIGN KEY (id_etudiant) REFERENCES etudiant(id_etudiant)
);

-- Hierarchie 2 : enseignant (mere) <- encadrant_academique (fille, meme identifiant)
CREATE TABLE enseignant (
  id_enseignant INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL, prenom VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL, departement VARCHAR(100) NOT NULL,
  type VARCHAR(20) NOT NULL DEFAULT 'enseignant'        -- enseignant | encadrant
);
CREATE TABLE encadrant_academique (
  id_enseignant INT PRIMARY KEY,
  date_statut DATE NOT NULL,
  CONSTRAINT fk_encadrant_enseignant FOREIGN KEY (id_enseignant) REFERENCES enseignant(id_enseignant)
);

CREATE TABLE stage (
  id_stage     INT AUTO_INCREMENT PRIMARY KEY,
  id_etudiant  INT NOT NULL,
  id_encadrant INT NOT NULL,
  sujet        VARCHAR(255) NOT NULL,
  date_debut   DATE NOT NULL,
  date_fin     DATE NOT NULL,
  statut       VARCHAR(20) NOT NULL DEFAULT 'en_attente',
  CONSTRAINT fk_stage_stagiaire  FOREIGN KEY (id_etudiant)  REFERENCES stagiaire(id_etudiant),
  CONSTRAINT fk_stage_encadrant  FOREIGN KEY (id_encadrant) REFERENCES encadrant_academique(id_enseignant),
  CONSTRAINT ck_dates CHECK (date_fin >= date_debut)
);

CREATE TABLE suivi_bienetre (
  id_suivi    INT AUTO_INCREMENT PRIMARY KEY,
  id_stage    INT NOT NULL,
  date        DATE NOT NULL,
  niveau      INT NOT NULL,
  commentaire TEXT,
  CONSTRAINT fk_suivi_stage FOREIGN KEY (id_stage) REFERENCES stage(id_stage),
  CONSTRAINT ck_niveau CHECK (niveau BETWEEN 1 AND 5)
);

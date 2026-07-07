-- ============================================================
-- Swachh Bharat - Dynamic Multi-City Database Schema
-- ============================================================
-- CHANGES FROM ORIGINAL:
--   • wards table now has "city" column (was hardcoded Rabakavi)
--   • complaints table has "city", "latitude", "longitude" columns
--   • staff table has "city" column (staff manages their city only)
--   • workers table has "city" column
-- ============================================================

CREATE DATABASE IF NOT EXISTS swachh_bharat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE swachh_bharat;

-- ─── WARDS TABLE ──────────────────────────────────────────────────────────────
-- Replaces hardcoded Rabakavi ward list
CREATE TABLE IF NOT EXISTS wards (
    ward_id              INT AUTO_INCREMENT PRIMARY KEY,
    ward_name            VARCHAR(100)  NOT NULL,
    area_name            VARCHAR(150),
    city                 VARCHAR(100)  NOT NULL,   -- NEW: supports any city
    state                VARCHAR(100)  DEFAULT 'Karnataka',
    pincode              VARCHAR(10),
    boundary_coordinates LONGTEXT,                 -- GeoJSON polygon (optional)
    population           INT,
    created_at           TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city       (city),
    INDEX idx_city_ward  (city, ward_id)
);

-- ─── COMPLAINTS TABLE ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id   INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100)  NOT NULL,
    phone          VARCHAR(15)   NOT NULL,
    ward_id        INT,
    city           VARCHAR(100)  NOT NULL,         -- NEW
    state          VARCHAR(100)  DEFAULT 'Karnataka',
    complaint      TEXT          NOT NULL,
    latitude       DECIMAL(10,7),                  -- NEW: user GPS coords
    longitude      DECIMAL(10,7),                  -- NEW
    status         ENUM('Pending','In Progress','Resolved') DEFAULT 'Pending',
    created_at     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    resolved_at    TIMESTAMP,
    assigned_to    INT,                            -- worker_id FK
    FOREIGN KEY (ward_id) REFERENCES wards(ward_id) ON DELETE SET NULL,
    INDEX idx_city_status (city, status),
    INDEX idx_created     (created_at)
);

-- ─── STAFF TABLE ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff (
    staff_id   INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    username   VARCHAR(50)  UNIQUE NOT NULL,
    password   VARCHAR(64)  NOT NULL,             -- MD5 hash
    city       VARCHAR(100),                      -- NEW: staff manages this city
    state      VARCHAR(100) DEFAULT 'Karnataka',
    phone      VARCHAR(15),
    email      VARCHAR(100),
    role       ENUM('admin','supervisor','inspector') DEFAULT 'inspector',
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city)
);

-- ─── WORKERS TABLE ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workers (
    worker_id    INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    password     VARCHAR(64),
    ward_id      INT,
    city         VARCHAR(100),                    -- NEW
    phone        VARCHAR(15),
    vehicle_no   VARCHAR(20),
    active       TINYINT(1)   DEFAULT 1,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ward_id) REFERENCES wards(ward_id) ON DELETE SET NULL,
    INDEX idx_city (city)
);

-- ─── LOCATION SESSION LOG ─────────────────────────────────────────────────────
-- Tracks which cities users access from (analytics)
CREATE TABLE IF NOT EXISTS location_logs (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    city       VARCHAR(100),
    latitude   DECIMAL(10,7),
    longitude  DECIMAL(10,7),
    ip_address VARCHAR(45),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city)
);

-- ─── SAMPLE DATA: Belagavi Wards ──────────────────────────────────────────────
INSERT IGNORE INTO wards (ward_id, ward_name, area_name, city, pincode) VALUES
(1,  'Ward 1  - Shivaji Nagar',   'Shivaji Nagar',   'belagavi', '590001'),
(2,  'Ward 2  - Gandhi Nagar',    'Gandhi Nagar',    'belagavi', '590001'),
(3,  'Ward 3  - Nehru Nagar',     'Nehru Nagar',     'belagavi', '590002'),
(4,  'Ward 4  - Tilakwadi',       'Tilakwadi',       'belagavi', '590006'),
(5,  'Ward 5  - Dharwad Road',    'Dharwad Road',    'belagavi', '590003'),
(6,  'Ward 6  - Angol',           'Angol',           'belagavi', '590006'),
(7,  'Ward 7  - Hindwadi',        'Hindwadi',        'belagavi', '590011'),
(8,  'Ward 8  - Bogarves',        'Bogarves',        'belagavi', '590001'),
(9,  'Ward 9  - Shahpur',         'Shahpur',         'belagavi', '590003'),
(10, 'Ward 10 - Bharat Nagar',    'Bharat Nagar',    'belagavi', '590016');

-- ─── SAMPLE DATA: Mysuru Wards ────────────────────────────────────────────────
INSERT IGNORE INTO wards (ward_id, ward_name, area_name, city, pincode) VALUES
(101, 'Ward 1  - Devaraja',        'Devaraja',        'mysuru', '570001'),
(102, 'Ward 2  - Krishnaraj',      'Krishnaraj',      'mysuru', '570001'),
(103, 'Ward 3  - Chamaraja',       'Chamaraja',       'mysuru', '570004'),
(104, 'Ward 4  - Narasimharaja',   'Narasimharaja',   'mysuru', '570005'),
(105, 'Ward 5  - Hebbal',          'Hebbal',          'mysuru', '570017');

-- ─── SAMPLE DATA: Jamkhandi/Rabakavi Wards (original data preserved) ──────────
INSERT IGNORE INTO wards (ward_id, ward_name, area_name, city, pincode) VALUES
(201, 'Ward 1',  'Ward 1',  'rabakavi-banhatti', '587313'),
(202, 'Ward 2',  'Ward 2',  'rabakavi-banhatti', '587313'),
(203, 'Ward 3',  'Ward 3',  'rabakavi-banhatti', '587313'),
(204, 'Ward 4',  'Ward 4',  'rabakavi-banhatti', '587313'),
(205, 'Ward 5',  'Ward 5',  'rabakavi-banhatti', '587313'),
(206, 'Ward 6',  'Ward 6',  'rabakavi-banhatti', '587313'),
(207, 'Ward 7',  'Ward 7',  'rabakavi-banhatti', '587313'),
(208, 'Ward 8',  'Ward 8',  'rabakavi-banhatti', '587313'),
(209, 'Ward 9',  'Ward 9',  'rabakavi-banhatti', '587313'),
(210, 'Ward 10', 'Ward 10', 'rabakavi-banhatti', '587313'),
(211, 'Ward 11', 'Ward 11', 'jamkhandi',         '587301'),
(212, 'Ward 12', 'Ward 12', 'jamkhandi',         '587301');

-- ─── DEFAULT STAFF ────────────────────────────────────────────────────────────
INSERT IGNORE INTO staff (name, username, password, city, role) VALUES
('Admin Belagavi', 'admin_blg',  MD5('admin123'), 'belagavi',         'admin'),
('Admin Mysuru',   'admin_mys',  MD5('admin123'), 'mysuru',           'admin'),
('Admin Rabakavi', 'admin_rbk',  MD5('admin123'), 'rabakavi-banhatti','admin');

-- ─── ADD IMAGE SUPPORT (run this if DB already exists) ────────────────────────
-- ALTER TABLE complaints ADD COLUMN images TEXT DEFAULT NULL;

-- New table for complaint images (multiple images per complaint)
CREATE TABLE IF NOT EXISTS complaint_images (
    image_id     INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    filename     VARCHAR(255) NOT NULL,
    uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    INDEX idx_complaint (complaint_id)
);

-- Table for photos uploaded when resolving a complaint
CREATE TABLE IF NOT EXISTS resolved_images (
    image_id     INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    filename     VARCHAR(255) NOT NULL,
    uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    INDEX idx_complaint (complaint_id)
);

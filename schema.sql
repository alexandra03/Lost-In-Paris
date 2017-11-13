CREATE TABLE phone (
    id INT(11) NOT NULL AUTO_INCREMENT,
    number VARCHAR(15) UNIQUE
);

CREATE TABLE location (
    address VARCHAR(140),
    alias VARCHAR(20),

    phone_id INTEGER,
    FOREIGN KEY (phone_id) REFERENCES phone (id) ON DELETE CASCADE
);

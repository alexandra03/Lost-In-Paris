DROP TABLE IF EXISTS phone;
DROP TABLE IF EXISTS location;

CREATE TABLE phone (
    id INTEGER PRIMARY KEY,
    "number" VARCHAR(15) UNIQUE
);

CREATE TABLE location (
    address VARCHAR(140),
    alias VARCHAR(20),

    phone_id INTEGER,
    FOREIGN KEY (phone_id) REFERENCES phone (id) ON DELETE CASCADE
);

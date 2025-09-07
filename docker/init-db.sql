CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    phrase TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    phrase TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    camera_id TEXT NOT NULL,
    location TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    frame_path TEXT,
    face_path TEXT,
    encrypted BOOLEAN DEFAULT FALSE,
    signature TEXT,
    processed BOOLEAN DEFAULT FALSE,
    face_match JSONB
);

CREATE TABLE IF NOT EXISTS known_faces (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL,
    person_name TEXT NOT NULL,
    face_encoding JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_detections_timestamp ON detections(timestamp);
CREATE INDEX idx_detections_camera_id ON detections(camera_id);
CREATE INDEX idx_detations_phrase ON detections(phrase);
CREATE INDEX idx_blacklist_phrase ON blacklist(phrase);

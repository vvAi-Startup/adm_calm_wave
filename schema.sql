
CREATE TABLE users (
	id INTEGER NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	profile_photo_url VARCHAR(500), 
	created_at DATETIME, 
	last_access DATETIME, 
	active BOOLEAN, 
	account_type VARCHAR(50), 
	role VARCHAR(50), 
	dark_mode BOOLEAN, 
	notifications_enabled BOOLEAN, 
	auto_process_audio BOOLEAN, 
	audio_quality VARCHAR(20), 
	PRIMARY KEY (id), 
	UNIQUE (email)
)

;

CREATE TABLE user_devices (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	device_name VARCHAR(255) NOT NULL, 
	device_type VARCHAR(100), 
	ip_address VARCHAR(50), 
	connected_at DATETIME, 
	last_active DATETIME, 
	is_current BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE user_achievements (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	achievement_id INTEGER NOT NULL, 
	unlocked_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE audios (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	filename VARCHAR(500) NOT NULL, 
	file_path VARCHAR(1000), 
	duration_seconds INTEGER, 
	size_bytes BIGINT, 
	recorded_at DATETIME, 
	processed BOOLEAN, 
	processed_path VARCHAR(1000), 
	processing_time_ms BIGINT, 
	transcribed BOOLEAN, 
	transcription_text TEXT, 
	favorite BOOLEAN, 
	playlist_id INTEGER, 
	device_origin VARCHAR(255), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(playlist_id) REFERENCES playlists (id)
)

;

CREATE TABLE playlists (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	color VARCHAR(20), 
	created_at DATETIME, 
	"order" INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE statistics (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	date DATE NOT NULL, 
	total_recordings INTEGER, 
	total_recorded_seconds INTEGER, 
	total_processing_ms BIGINT, 
	audios_transcribed INTEGER, 
	total_app_usage_seconds INTEGER, 
	playlists_created INTEGER, 
	audios_deleted INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE events (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	event_type VARCHAR(100) NOT NULL, 
	created_at DATETIME, 
	details_json TEXT, 
	screen VARCHAR(100), 
	level VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE settings (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	"key" VARCHAR(100) NOT NULL, 
	value TEXT, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	title VARCHAR(100) NOT NULL, 
	message TEXT NOT NULL, 
	type VARCHAR(20), 
	is_read BOOLEAN, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE support_tickets (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	status VARCHAR(50), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE ticket_messages (
	id INTEGER NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	sender VARCHAR(50) NOT NULL, 
	message TEXT NOT NULL, 
	sent_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(ticket_id) REFERENCES support_tickets (id)
)

;
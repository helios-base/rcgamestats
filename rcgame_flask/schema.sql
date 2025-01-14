DROP TABLE IF EXISTS test_matche;
DROP TABLE IF EXISTS hosts;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS group_matches;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE test_matche (
left_team varchar(30),
light_team varchar(30),
Mcount int(100000)
);

CREATE TABLE group_matches (
group_id INTEGER PRIMARY KEY AUTOINCREMENT,
group_name varchar(255) UNIQUE,
group_time datetime,
left_team varchar(30),
right_team varchar(30),
group_memo text,
game_count INTEGER,
executed_count INTEGER DEFAULT 0
);

CREATE TABLE hosts (
host_id INTEGER PRIMARY KEY AUTOINCREMENT,
host_name varchar(30),
IP varchar(12),
is_standby varchar(10)
);

CREATE TABLE matches (
match_id INTEGER PRIMARY KEY AUTOINCREMENT,
group_id int(10),
match_index int(10),
host_name varchar(30),
start_time DATETIME,
end_time DATETIME,
left_team varchar(30),
right_team varchar(30),
left_score int(10),
right_score int(10),
processed VARCHAR(15) DEFAULT 'unexecuted',
log_directory_name varchar(255),
log_file varchar(255),
FOREIGN KEY (group_id) REFERENCES group_matches(group_id),
FOREIGN KEY (host_name) REFERENCES group_matches(host_name)
);

CREATE TABLE teams (
team_id INTEGER PRIMARY KEY AUTOINCREMENT,
team_name varchar(255) UNIQUE,
acceleration varchar(5),
filepass varchar(50),
team_memo text
);


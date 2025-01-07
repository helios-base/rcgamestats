DROP TABLE IF EXISTS test_matche;
DROP TABLE IF EXISTS hosts;
DROP TABLE IF EXISTS matches;
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
Mcount int(10000)
);

CREATE TABLE hosts (
host_id AUTO_INCREMENT PRIMARY KEY,
host_name varchar(30),
IP varchar(12),
flag varchar(10)
);

CREATE TABLE matches (
match_id AUTO_INCREMENT PRIMARY KEY,
group_id int(10),
host verchar(30),
left_score int(10),
right_score int(10),
FOREIGN KEY (group_id) REFERENCES group_matchs(group_id)
);

CREATE TABLE teams (
team_id INTEGER PRIMARY KEY AUTOINCREMENT,
team_name varchar(255) UNIQUE,
acceleration varchar(5),
filepass varchar(50),
team_memo text
);


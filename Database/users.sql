-- add default users to the dnsconf database

TRUNCATE users;

INSERT INTO users(username,userpriv,userwho) VALUES
	('paul','Edit','Paul Hoffman'),
	('john','Edit','John Levine'),
	('scott','Edit','Scott Dawson'),
	('demo',NULL,'Demo User');

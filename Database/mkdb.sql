-- create tables in the database
DROP DATABASE IF EXISTS dnsconf;
CREATE DATABASE dnsconf;
USE dnsconf;

CREATE USER 'dnsconf' IDENTIFIED BY 'NitPicky';
CREATE USER 'dnsconf'@'localhost' IDENTIFIED BY 'NitPicky';
CREATE USER 'dnscuser'@'localhost' IDENTIFIED BY 'NitPickier';

GRANT ALL ON dnsconf.* to 'dnsconf';
GRANT ALL ON dnsconf.* to 'dnsconf'@'localhost';
GRANT INSERT,SELECT,DELETE,EXECUTE,UPDATE ON dnsconf.* to 'dnscuser';
GRANT INSERT,SELECT,DELETE,EXECUTE,UPDATE ON dnscuser.* to 'dnscuser'@'localhost';

CREATE TABLE users (
	username VARCHAR(20) NOT NULL PRIMARY KEY,
	userpriv SET('Edit','Comment','Clone'),
	userwho TINYTEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE basedoc (
	bdseqno INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	bdname VARCHAR(255) NOT NULL,
	bddoctype ENUM('None', 'RFC','TestPlan','RRtypeTemplate','Other') DEFAULT 'None',
	bdrfcno INT UNSIGNED,
	bdtext MEDIUMTEXT NOT NULL,
	bderrata TEXT,
	bdediff TEXT,
	bdthstat ENUM('None','Testable') DEFAULT 'None',
	bdcomment TEXT,
	bddstat ENUM('None','Active','Removed','Replaced') DEFAULT 'Active',
	bduser VARCHAR(20) NOT NULL REFERENCES users(username),
	bdupdated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	bdadded TIMESTAMP NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE basedoc_history LIKE basedoc;
ALTER TABLE basedoc_history CHANGE bdseqno bdseqno INT UNSIGNED, DROP PRIMARY KEY;

CREATE TABLE requirement (
	rseqno INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	bdseqno INT NOT NULL REFERENCES basedoc(bdseqno),
	rsameas INT UNSIGNED REFERENCES requirement(rseqno),
	rstart INT UNSIGNED NOT NULL,
	rlength INT UNSIGNED NOT NULL,
	rtext TEXT,
	rtype ENUM('None','Testable','Format','Operational','HighVol','LongPeriod','FutureSpec','Procedural','Historic','API','AppsAndPeople') DEFAULT 'None',
	rcomment TEXT,
	rreplacedby INT UNSIGNED REFERENCES requirement(rseqno),
	ruser VARCHAR(20) NOT NULL REFERENCES users(username),
	rupdated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	radded TIMESTAMP NOT NULL DEFAULT 0,
	UNIQUE KEY bdrange (bdseqno, rstart, rlength)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE requirement_history LIKE requirement;
ALTER TABLE requirement_history CHANGE rseqno rseqno INT UNSIGNED, DROP PRIMARY KEY, DROP KEY bdrange;

CREATE TABLE tests (
	tseqno INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	rseqno INT UNSIGNED NOT NULL REFERENCES requirement(rseqno),
	tsameas INT UNSIGNED REFERENCES tests(tseqno),
	ttext TEXT,
	tdut ENUM('None','Client','Server','Masterfile','Caching','Proxy','Recursive','SecResolv','Any','StubResolv','Validator', 'Signer','SecStub') DEFAULT 'None',
	tlscommand TEXT,
	toutcome TEXT,
	tneg ENUM('None', 'Negative') DEFAULT 'None',
	tcomment TEXT,
	tmasterfile TEXT,
	treplacedby INT UNSIGNED REFERENCES tests(tseqno),
	tuser VARCHAR(20) NOT NULL REFERENCES users(username),
	tupdated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	tadded TIMESTAMP NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE tests_history LIKE tests;
ALTER TABLE tests_history CHANGE tseqno tseqno INT UNSIGNED, DROP PRIMARY KEY;

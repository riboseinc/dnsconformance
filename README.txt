DNS Conformance Suite and Test Harness
   Version: 2015-08-13-00-37-11

The DNS Conformance Suite and Test Harness package is a complete conformance test system
for all parts of the DNS. The package:

- Identifies all of the RFCs and associated documents that contain DNS conformance requirements

- Separates those requirements out into a test plan

- Creates a test system for all parts of the test plan

Different enterprises and vendors will have different views of what should or should not
be tested, so the conformance test system allows easy selection of subsets of requirements
to be tested. The entire system is made available under Creative Commons licenses so that
anyone can use it and adapt it for local requirements.  In addition, the overall test
system is able to serve as the basis for creating conformance tests for other protocols.

The project was created by Standcore. Due to its scale, this project was supported by
multiple sponsors. The sponsors are:
 Akamai
 Dyn
 Google
 ICANN
 Infoblox
 Microsoft
 Verisign

==========

The heart of the project is a database of all the RFCs and other documents that specify
the current DNS. That database has an interactive web front-end and associated tools for
marking up the requirements in the RFCs, and specifying tests for each requirement. The
database can be turned into an HTML-formatted test plan that can be used to test
conformance to the DNS specifications.

We assumed that people might disagree on some of the requirements in the RFCs, and might
have different ideas about what tests to run for some requirements. Anyone can modify
their own copy of the database and create their own test plans from their database.
Because the test plans are valid structured HTML, comparing test plans is easy with any
file comparison tool, particularly ones that are optimized for comparing HTML files.

==========

The setup instructions below creates a full system on a local host. The instructions are
known to work well on Ubuntu Server 1404LTS, and will mostly work on Ubuntu Server 1504
but with some minor changes in the MySQL setup. When complete, the web front end will be
available at the following URLs (which can easily be changed in the Apache setup):

- List of documents: https://yourdomainname:44317/

- An individual document: https://yourdomainname:44317/document.htm?id=somenumber

- Console for searching and larger editing: https://yourdomainname:44318/

Note that the views for the list of documents and individual documents have an "Admin"
menu near the upper right with many commands, including "Help".

==========

Add software for Ubuntu:

	sudo apt-get update
	sudo apt-get dist-upgrade
	# This updates the kernel, so a reboot is a good idea here
	sudo apt-get install python3-pip
	sudo pip3 install bottle PyMySQL dnspython3

Get the distribuition tarball dnsconformance.tgz:

	wget https://www.standcore.com/dnsconformance.tgz
	tar -xzf dnsconformance.tgz

Initialize MySQL:

	sudo apt-get install mysql-server
		# Set the root password during installation here, or do so in the next step
	sudo /usr/bin/mysql_secure_installation
		# Answer questions to remove some of the default stuff
	# Edit /etc/mysql/my.cnf
		# Change myisam-recover to BACKUP,FORCE
		# Possibly turn on logging
	sudo update-rc.d mysql defaults
	sudo service mysql restart
	mysql -u root --password=TheRootPasswordYouChose < dnsconformance/Database/mkdb.sql
	mysql -u dnsconf --password=NitPicky dnsconf < dnsconformance/dnsconformance-database.sql
	# A useful alias for logging into the command line is:
	# alias MySQL='mysql -u dnsconf --password=NitPicky dnsconf'
	# If you change the password for the dnsconf user, be sure to also change it
	#    at the top of the conformdb.py file

Set up Apache:

	sudo apt-get install apache2
	sudo rm /etc/apache2/sites-enabled/000-default.conf  # To remove the default site
	sudo cp dnsconformance/WebContent/Conformance.conf.proto /etc/apache2/sites-enabled/Conformance.conf
	# Edit /etc/apache2/sites-enabled/Conformance.conf to change the defines at the top
	# Create a directory for web certs, set the permissions to be read-only for non-root, and install certs there
	# Typical is
		# sudo openssl genrsa -out your.domain.name.key 2048
		# sudo openssl req -new -sha1 -key your.domain.name.key -out your.domain.name.csr # Be sure to give a commonName
		# Then get the cert from a CA, or create a self-signed one:
			# sudo openssl x509 -req -days 1000 -in your.domain.name.csr -signkey your.domain.name.key -out your.domain.name.cer
	# Both the "cgi" and "ssl" modules need to be loaded; this is unfortunately distro-dependent
	sudo service apache2 restart
	# At this point, you can connect to https://YourIPAddress:44317 to see the list of documents in the test harness

==========

The database contains explicit tests for DNS clients and servers, and can be extended for more.
The Database/ directory of the distribution has a program called "extract-tests-from-database.py",
which retrieves all the explicit tests for different types of DNS systems (clients, recursive servers,
authoritative servers, and so on). More information is given in the help text for that command.

==========

Copyright (c) 2015, Standcore LLC
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions, and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions, and the following disclaimer in the documentation and/or
other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

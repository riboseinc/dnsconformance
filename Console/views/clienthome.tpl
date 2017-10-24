<!doctype html public "-//IETF//DTD HTML//EN">
<html>
<head>
<title>{{name}}</title>
<link rel=stylesheet type="text/css" href="/static/console.css">
</head>
<body>
    {{!boilerplate}}
<h1>DNS conformance suite database management</h1>
<p>Standcore sponsors have two choices for viewing or editing the DNS conformance database:
<ul>
<li>You can look at, but not modify, the live database being used by Standcore.</li>
<li>You can clone the live database and edit in a private sandbox.</li>
</ul>
</p>

<p>The snapshot starts with a copy of the live database, and has all the
same features as the live database.
You can switch back and forth between viewing the live database and editing in your sandbox database with the buttons below.</p>

<p>At any time you can reinitialize your sandbox with the contents of the live
database, so feel free to experiment.</p>

<form action="/snap" method="post">
<table align="center" cellpadding="5">
<tr><td><p><input type="submit" name="l" value="Live"/></p></td>
<td><p>Switch to viewing the live database</p></td></tr>
<tr><td><p><input type="submit" name="c" value="Sandbox"/></p></td>
<td><p>Switch to editing your sandbox database</p></td></tr>
<tr><td><p><input type="submit" name="r" value="Reinit"/></p></td>
<td><p>Reinitialize your sandbox and switch to editing the sandbox database<p></td></tr>
</table>
</form>
</body>
</html>

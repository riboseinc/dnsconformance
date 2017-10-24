%rebase('consolebase.tpl', name="Patch tests")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>Patch tests</p>

<p>
<form action="/whacktest" method="post">
<table>
<tr><th class="h" colspan=2>Patch tests</th><tr>
<tr><td class="e">Fields</td><td class="v"><input type="checkbox" name="ttext" checked/>ttext |
	<input type="checkbox" name="tlscommand" checked/>tlscommand |
	<input type="checkbox" name="toutcome" checked/>toutcome |
	<input type="checkbox" name="tcomment" checked/>tcomment</td></tr>
	<input type="checkbox" name="tmasterfile" checked/>tmasterfile</td></tr>
<tr><td class="e">Old string</td><td class="v"><input type="text" name="old" size=50 value="{{old}}"/></td></tr>
<tr><td class="e">New string</td><td class="v"><input type="text" name="new" size=50 value="{{new}}"/></td></tr>
<tr><td class="e">&nbsp;</td><td class="v"><input type="submit" name="Check" value="Check" />
	<input type="submit" name="Patch" value="Patch" /></td></tr>
</table>
</form></p>

</center>

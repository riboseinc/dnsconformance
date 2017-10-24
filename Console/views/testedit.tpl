%rebase('consolebase.tpl', name="Test")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>
<form action="/testedit/{{seqno}}" method="post">
<table>
<tr><td class="e">&nbsp;</td><td class="v"><input type="submit" name="Update" value="Update" /></td></tr>
<tr><th class="h" colspan=2>Edit test</th><tr>
  {{!reqtable}}
</table>
</form></p>

</center>

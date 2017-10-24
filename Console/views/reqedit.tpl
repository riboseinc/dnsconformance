%rebase('consolebase.tpl', name="Requirement")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>Edit requirement</p>

<p>
<form action="/reqedit/{{seqno}}" method="post">
<table>
<tr><td class="e">&nbsp;</td><td class="v"><input type="submit" name="Update" value="Update" /></td></tr>
<tr><th class="h" colspan=2>Edit requirement</th><tr>
  {{!reqtable}}
</table>
</form></p>

</center>

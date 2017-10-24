%rebase('consolebase.tpl', name="Base documents")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>Edit {{docname}}</p>

<p>
<form action="/bdedit/{{docno}}" method="post">
<table>
<tr><th class="h" colspan=2>Edit base document</th><tr>
  {{!doctable}}
<tr><td class="e">&nbsp;</td><td class="v"><input type="submit" name="Update" value="Update" /></td></tr>
</table>
</form></p>

</center>

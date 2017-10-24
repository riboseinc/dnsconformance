%rebase('consolebase.tpl', name="Requirement differences")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>Edit requirement</p>

<p>
<form action="/diff" method="get">
<table>
<tr><th class="h" colspan=2>Requirement differences vs {{clone}}</th><tr>
  {{!reqtable}}
</table>
</form></p>

</center>

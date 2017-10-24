%rebase('consolebase.tpl', name="Test differences")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>
<form action="/" method="get">
<table>
<tr><th class="h" colspan=2>Test differences vs {{clone}}</th><tr>
  {{!testtable}}
</table>
</form></p>

</center>

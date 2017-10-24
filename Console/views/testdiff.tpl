%rebase('consolebase.tpl', name="Test differences")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=5>Changed tests for {{clone}}</th><tr>
<tr><th class="h">Seqno</th>
    <th class="h">DUT</th>
    <th class="h">Text</th>
    <th class="h">Comment</th>
    <th class="h">LSCommand</th>
</tr>
  {{!dtesttable}}
<tr><th class="h" colspan=5>New tests for {{clone}}</th><tr>
<tr><th class="h">Seqno</th>
    <th class="h">DUT</th>
    <th class="h">Text</th>
    <th class="h">Comment</th>
    <th class="h">LSCommand</th>
</tr>
  {{!ctesttable}}
</table></p>

</center>

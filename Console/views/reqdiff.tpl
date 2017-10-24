%rebase('consolebase.tpl', name="Requirements differences")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=7>Changed requirements for {{clone}}</th><tr>
<tr><th class="h">Seqno</th>
    <th class="h">Start/Len</th>
    <th class="h">Sameas</th>
    <th class="h">Tests</th>
    <th class="h">Type</th>
    <th class="h">Text</th>
    <th class="h">Comment</th>
</tr>
  {{!dreqtable}}
<tr><th class="h" colspan=7>New requirements for {{clone}}</th><tr>
<tr><th class="h">Seqno</th>
    <th class="h">Start/Len</th>
    <th class="h">Sameas</th>
    <th class="h">Tests</th>
    <th class="h">Type</th>
    <th class="h">Text</th>
    <th class="h">Comment</th>
</tr>
  {{!creqtable}}
</table></p>

</center>

%rebase('consolebase.tpl', name="Tests")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=5>Base docs with tests</th><tr>
<tr><th class="h"># tests</th>
    <th class="h">RFC</th>
    <th class="h">Type</th>
    <th class="h">Status</th>
    <th class="h">Name</th>
</tr>
  {{!testtable}}
</table></p>

</center>

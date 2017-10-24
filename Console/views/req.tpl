%rebase('consolebase.tpl', name="Requirements")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=5>Requirements</th><tr>
<tr><th class="h"># reqs</th>
    <th class="h">RFC</th>
    <th class="h">Type</th>
    <th class="h">Status</th>
    <th class="h">Name</th>
</tr>
  {{!reqtable}}
</table></p>

</center>

%rebase('consolebase.tpl', name="Base documents")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=6>Base documents</th><tr>
<tr><th class="h"><a href="{{url}}?s=0">RFC</a></th>
    <th class="h"><a href="{{url}}?s=1">Type</a></th>
    <th class="h"><a href="{{url}}?s=2">Status</a></th>
    <th class="h"><a href="{{url}}?s=3">Testable?</a></th>
    <th class="h"><a href="{{url}}?s=4">Name</a></th>
    <th class="h">Edit</th>
</tr>
  {{!doctable}}
</table></p>

</center>

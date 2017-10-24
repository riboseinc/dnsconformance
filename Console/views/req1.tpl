%rebase('consolebase.tpl', name="Requirements")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=7>Requirements for {{bdname}}</th><tr>
<tr><th class="h"><a href="{{url}}?s=0">Seqno</a></th>
    <th class="h"><a href="{{url}}?s=1">Start/Len</a></th>
    <th class="h"><a href="{{url}}?s=2">Sameas</a></th>
    <th class="h"><a href="{{url}}?s=3">Tests</a></th>
    <th class="h"><a href="{{url}}?s=4">Type</a></th>
    <th class="h"><a href="{{url}}?s=5">Text</a></th>
    <th class="h"><a href="{{url}}?s=6">Comment</a></th>
</tr>
  {{!reqtable}}
</table></p>

</center>

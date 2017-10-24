%rebase('consolebase.tpl', name="Scan tests")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=2>Scan all tests</th><tr>
<tr><th class="h"><a href="{{url}}?s=0">Seqno</a></th>
    <th class="h"><a href="{{url}}?s=1">DUT</a>
    <a href="{{url}}?s=2">Text</a>
    <a href="{{url}}?s=3">Comment</a>
    <a href="{{url}}?s=4">Masterfile</a>
    <a href="{{url}}?s=5">LSCommand</a>
    <a href="{{url}}?s=6">Outcome</a></th>
</tr>
  {{!testtable}}
</table></p>

</center>

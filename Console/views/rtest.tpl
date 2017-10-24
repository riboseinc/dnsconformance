%rebase('consolebase.tpl', name="Selected tests")
{{!boilerplate}}
<center>
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p><table>
<tr><th class="h" colspan=5>Tests for {{tty}}</th><tr>
<tr><th class="h"><a href="{{url}}?s=0">Seqno</a></th>
    <th class="h"><a href="{{url}}?s=1">DUT</a></th>
    <th class="h"><a href="{{url}}?s=2">Text</a></th>
    <th class="h"><a href="{{url}}?s=3">Comment</a></th>
    <th class="h"><a href="{{url}}?s=4">LSCommand</a></th>
</tr>
  {{!testtable}}
</table></p>

</center>

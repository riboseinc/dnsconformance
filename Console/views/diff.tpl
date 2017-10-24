%rebase('consolebase.tpl', name="Look at differences")
{{!boilerplate}}
<center>
%if defined('kvetch'):
    <p><font color="red">{{!kvetch}}</font></p>
%end

<p>
<form action="/diff" method="post">
<table>
<tr><th class="h" colspan=2>Check for differences</th><tr>
<tr><td class="e">Clone:</td><td class="v"><select name="clone" size="1">{{!cloneopts}}</select></td></tr>
<tr><td class="e">Items:</td><td class="v"><select name="w" size="1"><option value="b">Base documents</option>
		<option value="r">Requirements</option><option value="t">Tests</option></select></td></tr>
<tr><td class="e">&nbsp;</td><td class="v"><input type="submit" name="diff" value="Get diffs" /></td></tr>
</tr>
</table></p>

</center>

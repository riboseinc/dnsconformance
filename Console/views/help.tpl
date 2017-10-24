%rebase('consolebase.tpl', name="Help")
{{!boilerplate}}
<center>
%if defined('helptext') and helptext:
    <div align=left>{{!helptext}}</div>
%end
</center>

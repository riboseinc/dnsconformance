%rebase('consolebase.tpl', name="Status")
{{!boilerplate}}
<center>
%if defined('kvetch') and kvetch:
    <p>{{!kvetch}}</p>
%end
</center>

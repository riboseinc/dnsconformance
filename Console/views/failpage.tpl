%rebase('consolebase.tpl', name="Request failed")
{{!boilerplate}}
<center>
%if defined('kvetch') and kvetch:
    <p>{{!kvetch}}</p>
%end
</center>

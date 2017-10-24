%rebase('consolebase.tpl', name="DNS conformance console")
{{!boilerplate}}
<center>
%if defined('kvetch') and kvetch:
    <p>{{!kvetch}}</p>
%end
</center>
<h2>Using the console</h2>
<ul>
<li>Click Basedoc for a list of base documents, each has a clickable link to edit it.</li>
<li>Click All Reqs for a list of all requirements
<li>Click Search Reqs for a list of base documents that have requirements. Click the number
of requirements to see a list of them, each is clickable to edit it.</li>
<li>Click All Tests to see a list of all tests
<li>Click Search Tests to see a list of base documents that have tests.
The list of requirements also has a clickable count of tests for each requirement.</li>
</ul>
<h2>Caveats</h2>
<ul>
<li>It makes only the most rudimentary sanity checks, so think before you edit.</li>
<li>You currently can't add or delete anything, only edit items that exist.</li>
<li>You currently can't change the user or the creation date.</li>
</ul>

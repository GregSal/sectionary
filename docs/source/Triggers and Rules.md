# Triggers and Rules

## Basic Definitions

### Test

> A dynamically defined conditional statement which takes a single argument and
> returns a Boolean.

### Trigger

> One or more Tests which cause an action to be performed or stopped.
> Triggers have access to the Context in addition to whatever arguments are
> explicitly passed to them.
>
> - Returns a Boolean.

### Rule

> A Trigger-method pair, where the method is applied if the Trigger returns
  > True.
>
> - The output of the method will depend on the type of Rule.

## Trigger Types

<table><thead>
<th>Trigger</th><th>Description</th>
</thead></tbody>
<tr><td>Simple Trigger</td>
  <td>A single Test and method that takes a single argument and returns a
      Boolean.<br>
      <ul><li>Used by Rules to cause an action to be performed or stopped.
      </ul></td></tr>
<tr><td>Complex Trigger</td>
  <td>Multiple conditional statements which are compounded
      e.g. A and (B or C).</td></tr>
<tr><td>Contextual Trigger</td>
  <td>A Complex Trigger that sets or updates Context attributes when one of
      it's conditional statements is evaluated.<br>
      Examples are:
      <ul>
        <li>A re.Match object from a Regex application
        <li>A Counter being initialized, incremented or reset.
        </ul></td></tr>
<tr><td>Break Trigger</td>
  <td> A Trigger used to identify a Section Break.<br>
    Conditions include:<br>
    <ul>
      <li>Testing the Line for the presence of any of the strings in a list of
          strings.
      <li>A compiled Regex, which is true if the Regex achieves a match in the
          Line.
      <li>A specified number of lines after another condition passes.
      <li>A custom counter reaches a certain value e.g. number of lines or
          number of repetitions of some other condition passing.
    </ul>
    Break Triggers can also be instructed to add or update a value in the
    Context.</td></tr>
</tbody></table>

## Rule Types

<table><thead>
<th>Type</th><th>Description</th>
</thead></tbody>
<tr><td>Simple Rule</td>
  <td>A Simple Trigger-method pair, where the output type of the Rule is the
      same as the input argument type.<br>
    <ul>
      <li>If the Trigger returns True, the method is applied.
      <li>If the Trigger returns False, the output of the Rule will be the input
          argument.
      <li>Simple Rules can be chained, since the output matched the input.
      </ul></td></tr>
<tr><td>Complex Rule</td>
  <td>A Trigger-method pair, where the output of the Rule depends on the result
     of the Trigger Test(s).</td></tr>
<tr><td>Cleaning Rule</td>
  <td>A Simple Rule taking a string argument.<br>
    <ul>
      <li>The output of the method will be a Cleaned Line.
    </ul></td></tr>
<tr><td>Parsing Line Rule</td>
  <td>A Complex Rule taking a string argument.<br>
    <ul>
      <li>The output of the method will be <u>zero or more</u> Parsed Lines.
    </ul></td></tr>
<tr><td>Line Processing Rule</td>
  <td>A Trigger-method pair, both taking a single Parsed Line argument<br>
    <ul>
      <li>The output of the method will be <u>zero or more</u> Parsed Lines.
  </ul></td></tr>
</tbody></table>

## Object Types

<table><thead>
<th>Type</th><th>Description</th>
</thead></tbody>
<tr><td>Trigger</td>
  <td>One or more Tests which cause an action to be performed or stopped.
      Triggers have access to the Context in addition to whatever arguments are
      explicitly passed to them.<br>
    <ul>
      <li>Returns a Boolean.<br>
    </ul></td></tr>
<tr><td>TriggerEvent</td>
  <td>Stores information regarding the result of applying a Trigger.<br>
      Contains:<br>
    <ul>
      <li>The name of the Trigger.
      <li>The Trigger results (<i>True</i> or <i>False</u>)
      <li>The name of the Trigger Test. (Useful when the Trigger contains
          multiple Tests.)
      <li>The relevant value returned by the test.
    </ul></td></tr>
<tr><td>Rule</td>
  <td>A Trigger-method pair, both taking a single argument, where the method is
      applied if the Trigger returns True.<br>
    <ul>
      <li>The output of the method will depend on the type of Rule.
    </ul></td></tr>
<tr><td>Rule Set</td>
  <td>A sequence of Rules and a default method.<br>
    <ul>
      <li>each Rule in the sequence will be applied to the input until One of
          the rules triggers.
      <li>if no Rule triggers then the default method is applied.
      <li>Each of the Rules (and the default method) take the same input type
          and return the same output type.
    </ul></td></tr>
<tr><td>Section Break</td>
  <td>A Trigger used to identify the point in the Source at which a Section
      begins or ends.</td></tr>
</tbody></table>

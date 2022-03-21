# Glossary

## Iterator Object

<table>
<tr><td>Source Iterator</td>
  <td>An Iterator or Sequence that returns string type objects when it's
  <code>__next__()</code> method is called.</td></tr>
<tr><td>Cleaned Lines Iterator</td>
  <td>An Iterator or Sequence that returns Cleaned Lines when it's
  <code>__next__()</code> method is called.</td></tr>
<tr><td>Section Iterator</td>
  <td>An Iterator or Sequence that returns The Cleaned Lines that belong to a
  particular Section when it's
  <code>__next__()</code> method is called.</td></tr>
<tr><td>Parsed Line Iterator</td>
  <td>An Iterator or Sequence that returns Parsed Line Items that belong to a
  particular Line when it's
  <code>__next__()</code> method is called.</td></tr>
</table>

## Object

<table>
<tr><td>Context</td>
  <td>General Information about the Source, and the current state, which is
    globally accessible and updateable. This information may be used and / or
    updated by Rules, during Line Processing, Section entering and exiting
    etc.<br>
    A Section may add its own custom items to the Context. These Items will not
    be removed from the Context unless explicitly deleted. In this way
    Information obtained in one Section can be employed by Rules in a later
    section.<br>
    Examples:<br>
    <ul>
    <li>File name
    <li>File modification date
    <li>Read date
    <li>Number of lines processed
    <li>Number of lines skipped
    <li>Section type
    <li>A resettable counter
    </ul></td></tr>
<tr><td>Dialect</td>
  <td>Formatting parameters used to define parsing options for "standard lines"
  from the Source.</td><td>
 <tr><td>Trigger</td>
   <td>One or more conditional statements (tests) which are used by Rules to
     cause an action to be performed or stopped. Used by Rules to cause an
     action to be performed or stopped.<br>
     Triggers have access to the Context in addition to whatever arguments are
     explicitly passed to them.</td></tr>
  <tr><td>Rule</td>
    <td>A Trigger-method pair, where the method is applied if the Trigger
      returns True. The output of the method will depend on the type of
      Rule.</td><td>
</table>

## Data Groups

<table>
<tr><td>Source</td>
  <td>The origin of all text data to be read. Can be a text file or a text
    stream or a str variable.</td></tr>
<tr><td>Section Group</td>
  <td>A sequence of Formatted Sections</td></tr>
<tr><td>Section</td>
  <td>A portion of the Source with a distinct Start and End. Sections have
    Uniquely defined Rules</td></tr>
<tr><td>Line</td>
  <td>single <u>string type</u> item returned by the Source's
    <code>__next__()</code> method.</td></tr>
<tr><td>Parsed Line Item</td>
  <td>A single item from a Parsed Line Tuple</td></tr>
<tr><td>Empty Fields</td>
  <td>Parsed Line Item resulting from having two delimiters adjacent to each
    other in the original un-parsed string.</td></tr>
<tr><td>Processed Section Lines</td>
  <td>A sequential group Lines from the Source after all Parsing and Processing
    has been completed.</td></tr>
<tr><td>Section Lines</td>
  <td>A sequence of Cleaned Lines from the Source.</td></tr>
</table>

## Line Types

<table>
<tr><td>Cleaned Line</td>
  <td>A Line object after Source Cleaning has been Applied</td></tr>
<tr><td>Parsed Line</td>
  <td>A Tuple resulting from a string being sectioned into one or more
    parts.</td></tr>
<tr><td>Standard Line</td>
  <td>A string item that from the source that should have the Dialect parsing
    applied to it.</td></tr>
<tr><td>Special Line</td>
  <td>A string item that from the source that should have the Dialect parsing
    applied to it.<br>
    Special Lines are identified by a set of Rules and the corresponding method
    for that Rule should return a Parsed Line, which will be treated as if it
    had the Dialect parsing applied to it.</td></tr>
<tr><td>Processed Line</td>
<td>A Tuple resulting from applying Processing Rules to a Parsed Line</td></tr>
</table>

## Action

<table>
<tr><td>Dropping</td>
  <td>Ignoring an item while stepping through an iterator, i.e. neither
    applying any method to the item nor passing it on to the next stage in the
    iteration process. The equivalent of a continue statement in a
    loop.</td></tr>
<tr><td>Trimming</td>
  <td>Removing leading and training whitespace from a string.</td></tr>
<tr><td>Encoding Conversion </td>
<td>Converting a string between different text encoding, such as
  UTF-8 or ANSI.<br>
  Also includes symbol conversion, where, for example, non-ANSI characters are
  replaced with ANSI compatible text e.g. <i>cm³</i> → <i>cc</i>.</td></tr>
<tr><td>Delimiter Conversion</td>
  <td>Converting a complex Delimiter Pattern e.g. Fixed length columns or
    multi-character delimiters into a temporary single character delimiter that
    a Dialect can recognize.</td></tr>
<tr><td>Cleaning</td>
  <td>Pre-processing of all strings prior to Parsing.<br>
    Examples may include:<br>
      <ul>
      <li>Encoding Conversion
      <li>Delimiter Conversion
      <li>Trimming
      <li>Dropping blank lines
      </ul></td></tr>
<tr><td>Source Cleaning</td>
  <td>Pre-processing of all strings from the Source prior to Sending to the
    Section Manager.</td></tr>
<tr><td>Section Cleaning</td>
  <td>Pre-processing of all Section Lines prior to Parsing.</td></tr>
<tr><td>Parsing</td>
  <td>Breaking a string into one or more parts and returning a sequence of
    those parts</td></tr>
<tr><td>Processing</td>
  <td>Methods applied to Parsed Line Items.<br>
    Examples include:<br>
      <li>Converting strings to numbers, including, stripping Units
      <li>Converting Date Strings to datetime/date/time
      <li>Replacing certain patterns, such as Empty Fields, with
        None, N/A, or ''
      <li>Applying a secondary parsing to a Parsed Line Item.
      </ul>
    Sometimes in the context of entire Parsed Line</td></tr>
<tr><td>Standard Processing</td>
  <td>Methods applied to all Parsed Line Items.</td></tr>
<tr><td>Section Formatting</td>
  <td>A method applied to Section Lines.<br>
    Examples include:<br>
      <ul>
      <li>Converting Section Lines that are made of a list of length 2 Tuples
        to a Dictionary
      <li>Converting the Section Lines to a Pandas DataFrame along with some
        DataFrame operations (e.g. Defining Column Names, Defining an Index,
        Sorting, Transposing)
        </ul></td></tr>
<tr><td>Section Group Assembly</td>
  <td>Combining Formatted Sections <br>
    Examples include:<br>
      <ul>
      <li>Repeat Sections as dictionaries → Data Frame
      <li>Merging Dictionaries
      <lu>Flattening lists of lists
      </ul></td></tr>
<tr><td>Section Breaking</td><td>Starting or stopping a Section</td></tr>
<tr><td>Line Parser</td><td></td></tr>
</table>

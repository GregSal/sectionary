# Glossary
## Iterator Object
|Term|Definition|
|----|----------|
|Source Iterator|An Iterator or Sequence that returns string type objects when it's  `__next__()` method is called.|
|Cleaned Lines Iterator|An Iterator or Sequence that returns Cleaned Lines when it's  `__next__()` method is called.|
|Section Iterator|An Iterator or Sequence that returns The Cleaned Lines that belong to a particular Section when it's  `__next__()` method is called.|
|Parsed Line Iterator|An Iterator or Sequence that returns Parsed Line Items that belong to a particular Line when it's  `__next__()` method is called.|

## Object
<table>
<tr><td>Context</td>
<td><p>
General Information about the Source, and the current state, which is globally
accessible and updatable. This information may be used and / or updated byRules, during Line Processing,  Section entering and exiting etc. </p>

<p>A Section may add its own custom items to the Context. These Items will notbe removed from the Context unless explicitly deleted. In this way Information obtained in one Section can be employed by Rules in a later section.</p>
Examples:
<ul>
<li>File name</li>
<li>File modification date</li>
<li>Read date</li>
<li>Number of lines processed</li>
<li>Number of lines skipped</li>
<li>Section type</li>
<li>A resettable counter</li>
</ul></td></tr>

<tr><td>Dialect</td>
<td>Formatting parameters used to define parsing options for "standard lines" from the Source.</td></tr>

<tr><td>Trigger</td>
<td>One or more conditional statements (tests) which are used by Rules to cause an
  action to be performed or stopped.  Used by Rules to cause an action to be performed or stopped.  Triggers have access to the Context in addition to whatever arguments are explicitly passed to them.</td></tr>
<tr><td>Rule</td>
<td>A Trigger-method pair, where the method is applied if the Trigger returns True.  The output of the method will depend on the type of Rule.</td></tr>
</table>

## Data Groups
<table>
<tr><td>Source</td>
<td>The origin of all text data to be read. Can be a text file or a text stream or a str variable.</td></tr>
<tr><td>Section Group</td>
<td>A sequence of Formatted Sections</td></tr>
 <tr><td>Section</td>
 <td>A portion of the Source with a distinct Start and End. Sections have Uniquely
  defined Rules</td></tr>
<tr><td>Line</td>
<td>A single string type item returned by the Source's __next__() method.</td></tr>
<tr><td>Parsed Line Item</td>
<td>A single item from a Parsed Line Tuple</td></tr>
<tr><td>Empty Fields</td>
<td>Parsed Line Item resulting from having two delimiters adjacent to each other in the original un-parsed string.</td></tr>
<tr><td>Processed Section Lines</td>
<td>A sequential group Lines from the Source after all Parsing and Processing has been completed.</td></tr>
<tr><td>Section Lines</td>
<td>A sequence of Cleaned Lines from the Source.</td></tr>
</table>

## Line Types
<table border="1" cellpadding="0" cellspacing="0" valign="top" style="direction:ltr;
 border-collapse:collapse;border-style:solid;border-color:#A3A3A3;border-width:
 1pt;margin-left:.7083in">
 <tbody><tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.6458in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Cleaned
  Line</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:5.7979in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">A Line
  object after Source Cleaning has been Applied</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.6458in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Parsed
  Line</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:5.7979in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">A Tuple
  resulting from a string being sectioned into one or more parts </p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.6458in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Standard
  Line</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:5.7979in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">A
  string item that from the source that should have the Dialect parsing applied
  to it.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.6458in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Special
  Line</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:5.7979in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">A
  string item that from the source that should <span style="font-weight:bold;
  text-decoration:underline">not</span> have the Dialect parsing applied to it.</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Special
  Lines are identified by a set of Rules and the corresponding method for that
  Rule should return a Parsed Line, which will be treated as if it had the
  Dialect parsing applied to it.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.6458in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Processed
  Line</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:5.7979in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">A Tuple
  resulting from applying Processing Rules to a Parsed Line</p>
  </td>
 </tr>
</tbody></table>

## Action
<table border="1" cellpadding="0" cellspacing="0" valign="top" style="direction:ltr;
 border-collapse:collapse;border-style:solid;border-color:#A3A3A3;border-width:
 1pt;margin-left:.3333in">
 <tbody><tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Dropping</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Ignoring
  an item while stepping through an iterator, i.e. neither applying any method
  to the item nor passing it on to the next stage in the iteration
  process.<span style="mso-spacerun:yes">&nbsp; </span>The equivalent of a co
ntinue
  statement in a loop. </p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Trimming</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Removing leading
  and training whitespace from a string.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Encoding
  Conversion </p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Converting a
  string between different text encoding, such as UTF-8 or ANSI.</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Also
  includes symbol conversion, where, for example, non-ANSI characters are
  replaced with ANSI compatible text e.g. cm<span style="vertical-align:super">3</span>
  -&gt; cc.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Delimiter
  Conversion</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt">Converting a
  complex Delimiter Pattern e.g.<span style="mso-spacerun:yes">&nbsp; </span>
Fixed
  length columns or multi-character delimiters into a temporary single
  character delimiter that a Dialect can recognize.<span style="mso-spacerun:yes">&nbsp; </span></p>
 </td></tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Cleaning</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Pre-processing
  of all strings prior to Parsing.</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Examples
  may include:</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt">Encoding
  Conversion</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt">Delimiter
  Conversion</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt">Trimming</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt" lang="en-US">Dropping blank lines</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Source
  Cleaning</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Pre-processing
  of all strings from the Source prior to Sending to the Section Manager.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Section
  Cleaning</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Pre-processing
  of all Section Lines prior to Parsing.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Parsing</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Breaking
  a string into one or more parts and returning a sequence of those parts</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Processing</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Methods
  applied to Parsed Line Items.</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Examples
  include:</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt"><span lang="en-US">Converting strings to numbers, including, stripping </span><span lang="en-CA">Units</span></p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt">Converting
  Date Strings to datetime/date/time</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt" lang="en-US">Replacing certain patterns, such as Empty Fields, with None, N/A,
  or ''</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt" lang="en-US">Applying a secondary parsing to a Parsed Line Item.</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Sometimes
  in the context of entire Parsed Line</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Standard
  Processing</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Methods
  applied to all Parsed Line Items.</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Section
  Formatting</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">A
  method applied to Section Lines. </p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Examples
  include:</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt" lang="en-US">Converting Section Lines that are made of a list of length 2
  Tuples to a Dictionary</p>
  <p style="margin:0in;margin-left:.375in;font-family:Calibri;font-size:11.0pt" lang="en-US">Converting the Section Lines to a Pandas DataFrame along with some
  DataFrame operations (e.g. Defining Column Names, Defining an Index, Sorting,
  Transposing)</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Section
  Group Assembly</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Combining
  Formatted Sections </p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Examples</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Repeat
  Sections as dictionaries -&gt; Data Frame</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Merging
  Dictionaries</p>
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Flattening
  lists of lists</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Section
  Breaking</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Starting
  or stopping a Section</p>
  </td>
 </tr>
 <tr>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:1.5277in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">Line
  Parser</p>
  </td>
  <td style="border-style:solid;border-color:#A3A3A3;border-width:1pt;
  vertical-align:top;width:6.2902in;padding:2.0pt 3.0pt 2.0pt 3.0pt">
  <p style="margin:0in;font-family:Calibri;font-size:11.0pt" lang="en-US">&nbsp;</p>
  </td>
 </tr>
</tbody></table>

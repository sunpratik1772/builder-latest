# Node Detail

Generated from the live backend `NodeSpec` registry (`engine.registry.studio_manifest`).
This file documents every node: what it does, inputs, outputs, static UI metadata, and config parameters.

## Node Index

| Node | Display | Section | Use |
| --- | --- | --- | --- |
| `AGGREGATE` | Aggregate | `transform` | Group items and perform aggregations |
| `CODE` | Code | `transform` | Execute custom Python code |
| `EXECUTE_WORKFLOW` | Execute Workflow | `control` | Execute another workflow as sub-workflow |
| `FILTER` | Filter | `transform` | Keep only items that match conditions |
| `HTML_EXTRACT` | Html Extract | `integration` | Extract data from HTML |
| `HTTP_REQUEST` | Http Request | `integration` | Make HTTP API requests |
| `IF` | If | `control` | Route workflow conditionally based on comparison operations. Evaluates conditions and sends data to 'true' or 'false' output. |
| `ITEM_LISTS` | Item Lists | `transform` | Array/list operations |
| `JSON` | Json | `transform` | Parse and manipulate JSON data |
| `LIMIT` | Limit | `transform` | Limit the number of items |
| `LOOP_OVER_ITEMS` | Loop Over Items | `control` | Execute once for each item in input |
| `MERGE` | Merge | `control` | Combine data from multiple inputs using various merge strategies |
| `SCHEDULE_TRIGGER` | Schedule Trigger | `trigger` | Trigger workflow on schedule |
| `SET` | Set | `transform` | Add, remove, or modify fields in items |
| `SORT` | Sort | `transform` | Sort items by field values |
| `SPLIT_IN_BATCHES` | Split In Batches | `control` | Split items into batches for processing |
| `SPREADSHEET_FILE` | Spreadsheet File | `integration` | Read/write Excel and CSV files |
| `SWITCH` | Switch | `control` | Route items to different outputs based on rules |
| `WAIT` | Wait | `control` | Wait/delay execution |
| `WEBHOOK` | Webhook | `trigger` | Receive data via webhook |
| `XML` | Xml | `transform` | Parse and manipulate XML data |

## `AGGREGATE` — Aggregate

**Use:** Group items and perform aggregations

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `AGGREGATE` |
| Display name | Aggregate |
| UI section | `transform` |
| Palette order | `16` |
| Color | `#7C3AED` |
| Icon | `Layers` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to aggregate |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Aggregated results |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `group_by` | `array` | no | `json` | `[]` |  | Fields to group by |
| `aggregations` | `array` | yes | `json` | `[]` |  | Aggregation operations |

**Constraints**

- group_by empty means aggregate all items together
- Each aggregation creates one output field
- count operation doesn't require a field name

## `CODE` — Code

**Use:** Execute custom Python code

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `CODE` |
| Display name | Code |
| UI section | `transform` |
| Palette order | `15` |
| Color | `#8B5CF6` |
| Icon | `Code2` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | no | Items to process |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Processed items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `code` | `code` | yes | `code` | `# Access input items<br># items = input['items']<br># Process and return<br>return items` |  | Python code to execute. Access items via 'items' variable |
| `mode` | `string` | no | `text` | `run_once_for_all` | `run_once_for_all`, `run_once_for_each` | Execution mode |

**Constraints**

- Code must return items list or dict
- run_once_for_all processes all items together
- run_once_for_each runs code for each item separately

## `EXECUTE_WORKFLOW` — Execute Workflow

**Use:** Execute another workflow as sub-workflow

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `EXECUTE_WORKFLOW` |
| Display name | Execute Workflow |
| UI section | `control` |
| Palette order | `7` |
| Color | `#8B5CF6` |
| Icon | `Workflow` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | no | Data to pass to sub-workflow |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Sub-workflow output |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `workflow_id` | `string` | yes | `text` |  |  | ID of workflow to execute |
| `wait_for_completion` | `boolean` | no | `checkbox` | `True` |  | Wait for sub-workflow to complete |

**Constraints**

- Executes specified workflow with input data
- Returns output from sub-workflow
- Can be used to modularize complex workflows

## `FILTER` — Filter

**Use:** Keep only items that match conditions

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `FILTER` |
| Display name | Filter |
| UI section | `transform` |
| Palette order | `12` |
| Color | `#FF6D5A` |
| Icon | `Filter` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to filter |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Filtered items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `conditions` | `array` | yes | `json` | `[]` |  | Filter conditions |
| `combine_operation` | `string` | no | `text` | `AND` | `AND`, `OR` | How to combine multiple conditions |

**Constraints**

- Only items matching the conditions are kept
- Empty conditions means keep all items

## `HTML_EXTRACT` — Html Extract

**Use:** Extract data from HTML

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `HTML_EXTRACT` |
| Display name | Html Extract |
| UI section | `integration` |
| Palette order | `22` |
| Color | `#F59E0B` |
| Icon | `FileCode` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items containing HTML |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Extracted data |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `source_field` | `string` | no | `text` | `html` |  | Field containing HTML |
| `extraction_values` | `array` | yes | `json` | `[]` |  | Values to extract |

**Constraints**

- Uses CSS selectors to extract data from HTML
- Returns extracted values as new fields
- Useful for web scraping

## `HTTP_REQUEST` — Http Request

**Use:** Make HTTP API requests

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `HTTP_REQUEST` |
| Display name | Http Request |
| UI section | `integration` |
| Palette order | `20` |
| Color | `#10B981` |
| Icon | `Globe` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | no | Items to process |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | HTTP response data |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `method` | `string` | yes | `text` | `GET` | `GET`, `POST`, `PUT`, `DELETE`, `PATCH` | HTTP method |
| `url` | `string` | yes | `text` |  |  | URL to request |
| `headers` | `object` | no | `json` | `{}` |  | HTTP headers |
| `body` | `object` | no | `json` | `{}` |  | Request body (for POST/PUT/PATCH) |
| `options` | `object` | no | `json` | `{}` |  |  |

**Constraints**

- Executes HTTP request for each input item
- Use {{field}} syntax to interpolate values from items
- Returns response as items

## `IF` — If

**Use:** Route workflow conditionally based on comparison operations. Evaluates conditions and sends data to 'true' or 'false' output.

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `IF` |
| Display name | If |
| UI section | `control` |
| Palette order | `1` |
| Color | `#FF6D5A` |
| Icon | `GitBranch` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Input items to evaluate against conditions |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `True` | `object` | no | `` | Items that match the conditions |  |
| `False` | `object` | no | `` | Items that do not match the conditions |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `conditions` | `array` | yes | `json` | `[]` |  | List of comparison conditions to evaluate |
| `combine_operation` | `string` | no | `text` | `AND` | `AND`, `OR` | How to combine multiple conditions |
| `options` | `object` | no | `json` | `{}` |  | Additional options |

**Constraints**

- At least one condition must be defined
- Items matching all/any conditions go to 'true' output, others to 'false' output
- Empty input results in empty outputs on both branches

## `ITEM_LISTS` — Item Lists

**Use:** Array/list operations

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `ITEM_LISTS` |
| Display name | Item Lists |
| UI section | `transform` |
| Palette order | `17` |
| Color | `#3B82F6` |
| Icon | `List` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to process |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Processed items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `operation` | `string` | yes | `text` | `split` | `split`, `sort_array`, `unique`, `remove_duplicates`, `flatten`, `reverse`, `shuffle` | Array operation to perform |
| `field_name` | `string` | no | `text` |  |  | Field containing the array |
| `options` | `object` | no | `json` | `{}` |  |  |

**Constraints**

- split operation splits single item with array into multiple items
- Operations work on array fields within items
- Some operations like flatten work on nested arrays

## `JSON` — Json

**Use:** Parse and manipulate JSON data

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `JSON` |
| Display name | Json |
| UI section | `transform` |
| Palette order | `18` |
| Color | `#F59E0B` |
| Icon | `Braces` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to process |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Processed JSON data |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `operation` | `string` | yes | `text` | `parse` | `parse`, `stringify`, `extract` | JSON operation |
| `field_name` | `string` | no | `text` |  |  | Field containing JSON string (for parse) |
| `json_path` | `string` | no | `text` |  |  | Path to extract (dot notation) |

**Constraints**

- parse converts JSON strings to objects
- stringify converts objects to JSON strings
- extract pulls specific values from JSON

## `LIMIT` — Limit

**Use:** Limit the number of items

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `LIMIT` |
| Display name | Limit |
| UI section | `transform` |
| Palette order | `14` |
| Color | `#F59E0B` |
| Icon | `Scissors` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to limit |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Limited items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `max_items` | `integer` | yes | `number` | `1` |  | Maximum number of items to output |
| `keep` | `string` | no | `text` | `first` | `first`, `last` | Which items to keep |

**Constraints**

- Returns at most max_items items
- If input has fewer items than max_items, returns all

## `LOOP_OVER_ITEMS` — Loop Over Items

**Use:** Execute once for each item in input

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `LOOP_OVER_ITEMS` |
| Display name | Loop Over Items |
| UI section | `control` |
| Palette order | `5` |
| Color | `#10B981` |
| Icon | `Repeat` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to loop over |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Current item |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `batch_size` | `integer` | no | `number` | `1` |  | Number of items to process together |

**Constraints**

- Executes downstream nodes once per item
- batch_size > 1 processes multiple items together
- Use with care - can cause many executions

## `MERGE` — Merge

**Use:** Combine data from multiple inputs using various merge strategies

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `MERGE` |
| Display name | Merge |
| UI section | `control` |
| Palette order | `3` |
| Color | `#FF6D5A` |
| Icon | `Combine` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input1` | `object` | yes | First input data stream |  |
| `input2` | `object` | yes | Second input data stream |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Merged data |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `mode` | `string` | yes | `text` | `append` | `append`, `combine`, `choose_branch` | How to merge the data |
| `combine_by` | `string` | no | `text` | `matching_fields` | `matching_fields`, `position`, `all_combinations` | How to combine when mode=combine |
| `fields_to_match` | `array` | no | `json` | `[]` |  | Field names to match on (for matching_fields mode) |
| `output_type` | `string` | no | `text` | `keep_matches` | `keep_matches`, `keep_non_matches`, `keep_everything`, `enrich_input1`, `enrich_input2` | What to keep when combining |
| `clash_handling` | `string` | no | `text` | `prefer_input2` | `prefer_input1`, `prefer_input2`, `add_input_number` | Which input to prioritize on field clash |

**Constraints**

- Append mode concatenates all items from both inputs
- Combine mode merges items based on combine_by setting
- Choose branch mode outputs data from one input only

## `SCHEDULE_TRIGGER` — Schedule Trigger

**Use:** Trigger workflow on schedule

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `SCHEDULE_TRIGGER` |
| Display name | Schedule Trigger |
| UI section | `trigger` |
| Palette order | `1` |
| Color | `#EF4444` |
| Icon | `Calendar` |
| Config tags |  |

**Inputs**

No declared inputs.

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Trigger data with timestamp |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `mode` | `string` | yes | `text` | `interval` | `interval`, `cron` | Schedule mode |
| `interval` | `integer` | no | `number` | `60` |  | Interval in minutes (interval mode) |
| `cron_expression` | `string` | no | `text` |  |  | Cron expression (cron mode) |

**Constraints**

- Triggers workflow at specified intervals or cron schedule
- interval mode runs every N minutes
- cron mode uses standard cron syntax

## `SET` — Set

**Use:** Add, remove, or modify fields in items

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `SET` |
| Display name | Set |
| UI section | `transform` |
| Palette order | `10` |
| Color | `#0EA5E9` |
| Icon | `PenTool` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to transform |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Transformed items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `mode` | `string` | yes | `text` | `manual` | `manual`, `json` | How to set fields |
| `fields` | `array` | no | `json` | `[]` |  | Fields to set (manual mode) |
| `json_data` | `object` | no | `json` | `{}` |  | JSON object to merge (json mode) |
| `options` | `object` | no | `json` | `{}` |  | Additional options |

**Constraints**

- Manual mode sets individual fields one by one
- JSON mode merges entire JSON object into each item
- Dot notation allows setting nested fields like user.name

## `SORT` — Sort

**Use:** Sort items by field values

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `SORT` |
| Display name | Sort |
| UI section | `transform` |
| Palette order | `13` |
| Color | `#7C3AED` |
| Icon | `ArrowUpDown` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to sort |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Sorted items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `sort_by` | `array` | yes | `json` | `[]` |  | Fields to sort by |
| `options` | `object` | no | `json` | `{}` |  |  |

**Constraints**

- Items are sorted by first field, then second, etc.
- Supports nested field access with dot notation

## `SPLIT_IN_BATCHES` — Split In Batches

**Use:** Split items into batches for processing

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `SPLIT_IN_BATCHES` |
| Display name | Split In Batches |
| UI section | `control` |
| Palette order | `4` |
| Color | `#F59E0B` |
| Icon | `Package` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to batch |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Batch of items |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `batch_size` | `integer` | yes | `number` | `10` |  | Number of items per batch |
| `options` | `object` | no | `json` | `{}` |  |  |

**Constraints**

- Splits input into batches of batch_size items
- Last batch may have fewer items
- Node executes multiple times until all batches are processed

## `SPREADSHEET_FILE` — Spreadsheet File

**Use:** Read/write Excel and CSV files

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `SPREADSHEET_FILE` |
| Display name | Spreadsheet File |
| UI section | `integration` |
| Palette order | `21` |
| Color | `#10B981` |
| Icon | `FileSpreadsheet` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | no | Data to write (for write operation) |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | File data |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `operation` | `string` | yes | `text` | `read` | `read`, `write` | File operation |
| `file_format` | `string` | yes | `text` | `csv` | `csv`, `xlsx`, `json` | File format |
| `file_path` | `string` | no | `text` |  |  | Path to file |
| `options` | `object` | no | `json` | `{}` |  |  |

**Constraints**

- read operation returns rows as items
- write operation creates file from items
- Supports CSV, Excel, and JSON formats

## `SWITCH` — Switch

**Use:** Route items to different outputs based on rules

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `SWITCH` |
| Display name | Switch |
| UI section | `control` |
| Palette order | `2` |
| Color | `#F59E0B` |
| Icon | `GitBranch` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to route |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output0` | `object` | no | `` | Output 0 |  |
| `output1` | `object` | no | `` | Output 1 |  |
| `output2` | `object` | no | `` | Output 2 |  |
| `output3` | `object` | no | `` | Output 3 |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `mode` | `string` | yes | `text` | `rules` | `rules`, `expression` | Routing mode |
| `rules` | `array` | no | `json` | `[]` |  | Routing rules (rules mode) |
| `fallback_output` | `integer` | no | `number` | `0` |  | Output index for items that don't match any rule |

**Constraints**

- Each item is routed to one output only
- Rules are evaluated in order, first match wins
- Items not matching any rule go to fallback output

## `WAIT` — Wait

**Use:** Wait/delay execution

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `WAIT` |
| Display name | Wait |
| UI section | `control` |
| Palette order | `6` |
| Color | `#6B7280` |
| Icon | `Clock` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to pass through after waiting |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Items (unchanged) |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `amount` | `integer` | yes | `number` | `1` |  | Amount of time to wait |
| `unit` | `string` | yes | `text` | `seconds` | `seconds`, `minutes`, `hours` | Time unit |

**Constraints**

- Pauses execution for specified duration
- Items pass through unchanged
- Useful for rate limiting or scheduling

## `WEBHOOK` — Webhook

**Use:** Receive data via webhook

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `WEBHOOK` |
| Display name | Webhook |
| UI section | `trigger` |
| Palette order | `2` |
| Color | `#8B5CF6` |
| Icon | `Webhook` |
| Config tags |  |

**Inputs**

No declared inputs.

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Webhook payload |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `path` | `string` | no | `text` |  |  | Webhook path (auto-generated if empty) |
| `method` | `string` | no | `text` | `POST` | `GET`, `POST`, `PUT`, `DELETE`, `ANY` | HTTP method to accept |
| `response_mode` | `string` | no | `text` | `on_received` | `on_received`, `last_node`, `response_node` | How to respond to webhook |

**Constraints**

- Triggers workflow when webhook is called
- Returns webhook body as items
- Generates unique webhook URL

## `XML` — Xml

**Use:** Parse and manipulate XML data

**Static metadata**

| Field | Value |
| --- | --- |
| Type | `XML` |
| Display name | Xml |
| UI section | `transform` |
| Palette order | `19` |
| Color | `#F59E0B` |
| Icon | `Code` |
| Config tags |  |

**Inputs**

| Name | Type | Required | Description | Requirements |
| --- | --- | --- | --- | --- |
| `input` | `object` | yes | Items to process |  |

**Outputs**

| Name | Type | Optional | Stored at | Description | Requirements |
| --- | --- | --- | --- | --- | --- |
| `output` | `object` | no | `` | Processed XML data |  |

**Config parameters**

| Name | Type | Required | Widget | Default | Enum/options | Description |
| --- | --- | --- | --- | --- | --- | --- |
| `operation` | `string` | yes | `text` | `parse` | `parse`, `stringify`, `extract` | XML operation |
| `field_name` | `string` | no | `text` |  |  | Field containing XML string |
| `xpath` | `string` | no | `text` |  |  | XPath to extract |

**Constraints**

- parse converts XML strings to objects
- stringify converts objects to XML strings
- extract pulls specific values using XPath

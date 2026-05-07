/**
 * AUTO-GENERATED — do not edit by hand.
 * Run `python backend/scripts/gen_artifacts.py` to regenerate.
 * Source: backend/engine/registry.py
 */
import type { LucideIcon } from 'lucide-react'
import {
  ArrowUpDown,
  Braces,
  Calendar,
  Clock,
  Code,
  Code2,
  Combine,
  FileCode,
  FileSpreadsheet,
  Filter,
  GitBranch,
  Globe,
  Layers,
  List,
  Package,
  PenTool,
  Repeat,
  Scissors,
  Webhook,
  Workflow,
} from 'lucide-react'

export type NodeType =
  | 'AGGREGATE'
  | 'CODE'
  | 'EXECUTE_WORKFLOW'
  | 'FILTER'
  | 'HTML_EXTRACT'
  | 'HTTP_REQUEST'
  | 'IF'
  | 'ITEM_LISTS'
  | 'JSON'
  | 'LIMIT'
  | 'LOOP_OVER_ITEMS'
  | 'MERGE'
  | 'SCHEDULE_TRIGGER'
  | 'SET'
  | 'SORT'
  | 'SPLIT_IN_BATCHES'
  | 'SPREADSHEET_FILE'
  | 'SWITCH'
  | 'WAIT'
  | 'WEBHOOK'
  | 'XML'

export interface NodeUIMeta {
  color: string
  Icon: LucideIcon
  description: string
  /** Config keys whose values are rendered as chips on the node card. */
  configTags: readonly string[]
  /** Palette group id — must match PaletteSection.id */
  paletteGroup: string
  /** Sort key within the palette group (lower first). */
  paletteOrder: number
  /** Short card title; when omitted, UI title-cases type_id. */
  displayName?: string
}

export interface PaletteSection {
  id: string
  label: string
  order: number
  color: string
}

export const PALETTE_SECTIONS: readonly PaletteSection[] = [
  {
    "id": "trigger",
    "label": "Triggers",
    "order": 1,
    "color": "#EF4444"
  },
  {
    "id": "control",
    "label": "Control Flow",
    "order": 5,
    "color": "#FF6D5A"
  },
  {
    "id": "transform",
    "label": "Transform",
    "order": 20,
    "color": "#A78BFA"
  },
  {
    "id": "integration",
    "label": "Integration",
    "order": 30,
    "color": "#10B981"
  }
] as const

export const NODE_UI: Record<NodeType, NodeUIMeta> = {
  AGGREGATE: {
    color: '#7C3AED',
    Icon: Layers,
    description: "Group items and perform aggregations",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 16,
  },
  CODE: {
    color: '#8B5CF6',
    Icon: Code2,
    description: "Execute custom Python code",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 15,
  },
  EXECUTE_WORKFLOW: {
    color: '#8B5CF6',
    Icon: Workflow,
    description: "Execute another workflow as sub-workflow",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 7,
  },
  FILTER: {
    color: '#FF6D5A',
    Icon: Filter,
    description: "Keep only items that match conditions",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 12,
  },
  HTML_EXTRACT: {
    color: '#F59E0B',
    Icon: FileCode,
    description: "Extract data from HTML",
    configTags: [] as const,
    paletteGroup: "integration",
    paletteOrder: 22,
  },
  HTTP_REQUEST: {
    color: '#10B981',
    Icon: Globe,
    description: "Make HTTP API requests",
    configTags: [] as const,
    paletteGroup: "integration",
    paletteOrder: 20,
  },
  IF: {
    color: '#FF6D5A',
    Icon: GitBranch,
    description: "Route workflow conditionally based on comparison operations. Evaluates conditions and sends data to 'true' or 'false' output.",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 1,
  },
  ITEM_LISTS: {
    color: '#3B82F6',
    Icon: List,
    description: "Array/list operations",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 17,
  },
  JSON: {
    color: '#F59E0B',
    Icon: Braces,
    description: "Parse and manipulate JSON data",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 18,
  },
  LIMIT: {
    color: '#F59E0B',
    Icon: Scissors,
    description: "Limit the number of items",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 14,
  },
  LOOP_OVER_ITEMS: {
    color: '#10B981',
    Icon: Repeat,
    description: "Execute once for each item in input",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 5,
  },
  MERGE: {
    color: '#FF6D5A',
    Icon: Combine,
    description: "Combine data from multiple inputs using various merge strategies",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 3,
  },
  SCHEDULE_TRIGGER: {
    color: '#EF4444',
    Icon: Calendar,
    description: "Trigger workflow on schedule",
    configTags: [] as const,
    paletteGroup: "trigger",
    paletteOrder: 1,
  },
  SET: {
    color: '#0EA5E9',
    Icon: PenTool,
    description: "Add, remove, or modify fields in items",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 10,
  },
  SORT: {
    color: '#7C3AED',
    Icon: ArrowUpDown,
    description: "Sort items by field values",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 13,
  },
  SPLIT_IN_BATCHES: {
    color: '#F59E0B',
    Icon: Package,
    description: "Split items into batches for processing",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 4,
  },
  SPREADSHEET_FILE: {
    color: '#10B981',
    Icon: FileSpreadsheet,
    description: "Read/write Excel and CSV files",
    configTags: [] as const,
    paletteGroup: "integration",
    paletteOrder: 21,
  },
  SWITCH: {
    color: '#F59E0B',
    Icon: GitBranch,
    description: "Route items to different outputs based on rules",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 2,
  },
  WAIT: {
    color: '#6B7280',
    Icon: Clock,
    description: "Wait/delay execution",
    configTags: [] as const,
    paletteGroup: "control",
    paletteOrder: 6,
  },
  WEBHOOK: {
    color: '#8B5CF6',
    Icon: Webhook,
    description: "Receive data via webhook",
    configTags: [] as const,
    paletteGroup: "trigger",
    paletteOrder: 2,
  },
  XML: {
    color: '#F59E0B',
    Icon: Code,
    description: "Parse and manipulate XML data",
    configTags: [] as const,
    paletteGroup: "transform",
    paletteOrder: 19,
  },
}

export const NODE_TYPES: readonly NodeType[] = [
  'AGGREGATE',
  'CODE',
  'EXECUTE_WORKFLOW',
  'FILTER',
  'HTML_EXTRACT',
  'HTTP_REQUEST',
  'IF',
  'ITEM_LISTS',
  'JSON',
  'LIMIT',
  'LOOP_OVER_ITEMS',
  'MERGE',
  'SCHEDULE_TRIGGER',
  'SET',
  'SORT',
  'SPLIT_IN_BATCHES',
  'SPREADSHEET_FILE',
  'SWITCH',
  'WAIT',
  'WEBHOOK',
  'XML',
] as const

/** Schema + constraints for a node type, surfaced in the Config inspector. */
export interface NodeContract {
  description: string
  inputs: Record<string, string>
  outputs: Record<string, string>
  configSchema: Record<string, string>
  constraints: readonly string[]
}

export const NODE_CONTRACTS: Record<NodeType, NodeContract> = {
  AGGREGATE: {
    description: "Group items and perform aggregations",
    inputs: {
          "input": "Items to aggregate"
    },
    outputs: {
          "output": "Aggregated results"
    },
    configSchema: {
          "group_by": "Fields to group by",
          "aggregations": "Aggregation operations"
    },
    constraints: ["group_by empty means aggregate all items together", "Each aggregation creates one output field", "count operation doesn't require a field name"] as const,
  },
  CODE: {
    description: "Execute custom Python code",
    inputs: {
          "input": "Items to process"
    },
    outputs: {
          "output": "Processed items"
    },
    configSchema: {
          "code": "Python code to execute. Access items via 'items' variable",
          "mode": "Execution mode"
    },
    constraints: ["Code must return items list or dict", "run_once_for_all processes all items together", "run_once_for_each runs code for each item separately"] as const,
  },
  EXECUTE_WORKFLOW: {
    description: "Execute another workflow as sub-workflow",
    inputs: {
          "input": "Data to pass to sub-workflow"
    },
    outputs: {
          "output": "Sub-workflow output"
    },
    configSchema: {
          "workflow_id": "ID of workflow to execute",
          "wait_for_completion": "Wait for sub-workflow to complete"
    },
    constraints: ["Executes specified workflow with input data", "Returns output from sub-workflow", "Can be used to modularize complex workflows"] as const,
  },
  FILTER: {
    description: "Keep only items that match conditions",
    inputs: {
          "input": "Items to filter"
    },
    outputs: {
          "output": "Filtered items"
    },
    configSchema: {
          "conditions": "Filter conditions",
          "combine_operation": "How to combine multiple conditions"
    },
    constraints: ["Only items matching the conditions are kept", "Empty conditions means keep all items"] as const,
  },
  HTML_EXTRACT: {
    description: "Extract data from HTML",
    inputs: {
          "input": "Items containing HTML"
    },
    outputs: {
          "output": "Extracted data"
    },
    configSchema: {
          "source_field": "Field containing HTML",
          "extraction_values": "Values to extract"
    },
    constraints: ["Uses CSS selectors to extract data from HTML", "Returns extracted values as new fields", "Useful for web scraping"] as const,
  },
  HTTP_REQUEST: {
    description: "Make HTTP API requests",
    inputs: {
          "input": "Items to process"
    },
    outputs: {
          "output": "HTTP response data"
    },
    configSchema: {
          "method": "HTTP method",
          "url": "URL to request",
          "headers": "HTTP headers",
          "body": "Request body (for POST/PUT/PATCH)",
          "options": ""
    },
    constraints: ["Executes HTTP request for each input item", "Use {{field}} syntax to interpolate values from items", "Returns response as items"] as const,
  },
  IF: {
    description: "Route workflow conditionally based on comparison operations. Evaluates conditions and sends data to 'true' or 'false' output.",
    inputs: {
          "input": "Input items to evaluate against conditions"
    },
    outputs: {
          "true": "Items that match the conditions",
          "false": "Items that do not match the conditions"
    },
    configSchema: {
          "conditions": "List of comparison conditions to evaluate",
          "combine_operation": "How to combine multiple conditions",
          "options": "Additional options"
    },
    constraints: ["At least one condition must be defined", "Items matching all/any conditions go to 'true' output, others to 'false' output", "Empty input results in empty outputs on both branches"] as const,
  },
  ITEM_LISTS: {
    description: "Array/list operations",
    inputs: {
          "input": "Items to process"
    },
    outputs: {
          "output": "Processed items"
    },
    configSchema: {
          "operation": "Array operation to perform",
          "field_name": "Field containing the array",
          "options": ""
    },
    constraints: ["split operation splits single item with array into multiple items", "Operations work on array fields within items", "Some operations like flatten work on nested arrays"] as const,
  },
  JSON: {
    description: "Parse and manipulate JSON data",
    inputs: {
          "input": "Items to process"
    },
    outputs: {
          "output": "Processed JSON data"
    },
    configSchema: {
          "operation": "JSON operation",
          "field_name": "Field containing JSON string (for parse)",
          "json_path": "Path to extract (dot notation)"
    },
    constraints: ["parse converts JSON strings to objects", "stringify converts objects to JSON strings", "extract pulls specific values from JSON"] as const,
  },
  LIMIT: {
    description: "Limit the number of items",
    inputs: {
          "input": "Items to limit"
    },
    outputs: {
          "output": "Limited items"
    },
    configSchema: {
          "max_items": "Maximum number of items to output",
          "keep": "Which items to keep"
    },
    constraints: ["Returns at most max_items items", "If input has fewer items than max_items, returns all"] as const,
  },
  LOOP_OVER_ITEMS: {
    description: "Execute once for each item in input",
    inputs: {
          "input": "Items to loop over"
    },
    outputs: {
          "output": "Current item"
    },
    configSchema: {
          "batch_size": "Number of items to process together"
    },
    constraints: ["Executes downstream nodes once per item", "batch_size > 1 processes multiple items together", "Use with care - can cause many executions"] as const,
  },
  MERGE: {
    description: "Combine data from multiple inputs using various merge strategies",
    inputs: {
          "input1": "First input data stream",
          "input2": "Second input data stream"
    },
    outputs: {
          "output": "Merged data"
    },
    configSchema: {
          "mode": "How to merge the data",
          "combine_by": "How to combine when mode=combine",
          "fields_to_match": "Field names to match on (for matching_fields mode)",
          "output_type": "What to keep when combining",
          "clash_handling": "Which input to prioritize on field clash"
    },
    constraints: ["Append mode concatenates all items from both inputs", "Combine mode merges items based on combine_by setting", "Choose branch mode outputs data from one input only"] as const,
  },
  SCHEDULE_TRIGGER: {
    description: "Trigger workflow on schedule",
    inputs: {},
    outputs: {
          "output": "Trigger data with timestamp"
    },
    configSchema: {
          "mode": "Schedule mode",
          "interval": "Interval in minutes (interval mode)",
          "cron_expression": "Cron expression (cron mode)"
    },
    constraints: ["Triggers workflow at specified intervals or cron schedule", "interval mode runs every N minutes", "cron mode uses standard cron syntax"] as const,
  },
  SET: {
    description: "Add, remove, or modify fields in items",
    inputs: {
          "input": "Items to transform"
    },
    outputs: {
          "output": "Transformed items"
    },
    configSchema: {
          "mode": "How to set fields",
          "fields": "Fields to set (manual mode)",
          "json_data": "JSON object to merge (json mode)",
          "options": "Additional options"
    },
    constraints: ["Manual mode sets individual fields one by one", "JSON mode merges entire JSON object into each item", "Dot notation allows setting nested fields like user.name"] as const,
  },
  SORT: {
    description: "Sort items by field values",
    inputs: {
          "input": "Items to sort"
    },
    outputs: {
          "output": "Sorted items"
    },
    configSchema: {
          "sort_by": "Fields to sort by",
          "options": ""
    },
    constraints: ["Items are sorted by first field, then second, etc.", "Supports nested field access with dot notation"] as const,
  },
  SPLIT_IN_BATCHES: {
    description: "Split items into batches for processing",
    inputs: {
          "input": "Items to batch"
    },
    outputs: {
          "output": "Batch of items"
    },
    configSchema: {
          "batch_size": "Number of items per batch",
          "options": ""
    },
    constraints: ["Splits input into batches of batch_size items", "Last batch may have fewer items", "Node executes multiple times until all batches are processed"] as const,
  },
  SPREADSHEET_FILE: {
    description: "Read/write Excel and CSV files",
    inputs: {
          "input": "Data to write (for write operation)"
    },
    outputs: {
          "output": "File data"
    },
    configSchema: {
          "operation": "File operation",
          "file_format": "File format",
          "file_path": "Path to file",
          "options": ""
    },
    constraints: ["read operation returns rows as items", "write operation creates file from items", "Supports CSV, Excel, and JSON formats"] as const,
  },
  SWITCH: {
    description: "Route items to different outputs based on rules",
    inputs: {
          "input": "Items to route"
    },
    outputs: {
          "output0": "Output 0",
          "output1": "Output 1",
          "output2": "Output 2",
          "output3": "Output 3"
    },
    configSchema: {
          "mode": "Routing mode",
          "rules": "Routing rules (rules mode)",
          "fallback_output": "Output index for items that don't match any rule"
    },
    constraints: ["Each item is routed to one output only", "Rules are evaluated in order, first match wins", "Items not matching any rule go to fallback output"] as const,
  },
  WAIT: {
    description: "Wait/delay execution",
    inputs: {
          "input": "Items to pass through after waiting"
    },
    outputs: {
          "output": "Items (unchanged)"
    },
    configSchema: {
          "amount": "Amount of time to wait",
          "unit": "Time unit"
    },
    constraints: ["Pauses execution for specified duration", "Items pass through unchanged", "Useful for rate limiting or scheduling"] as const,
  },
  WEBHOOK: {
    description: "Receive data via webhook",
    inputs: {},
    outputs: {
          "output": "Webhook payload"
    },
    configSchema: {
          "path": "Webhook path (auto-generated if empty)",
          "method": "HTTP method to accept",
          "response_mode": "How to respond to webhook"
    },
    constraints: ["Triggers workflow when webhook is called", "Returns webhook body as items", "Generates unique webhook URL"] as const,
  },
  XML: {
    description: "Parse and manipulate XML data",
    inputs: {
          "input": "Items to process"
    },
    outputs: {
          "output": "Processed XML data"
    },
    configSchema: {
          "operation": "XML operation",
          "field_name": "Field containing XML string",
          "xpath": "XPath to extract"
    },
    constraints: ["parse converts XML strings to objects", "stringify converts objects to XML strings", "extract pulls specific values using XPath"] as const,
  },
}

/** Typed port — what flows along an edge. */
export interface NodePortSpec {
  name: string
  type: 'dataframe' | 'scalar' | 'object' | 'text'
  description: string
  optional: boolean
  required_columns?: readonly string[]
  required_keys?: readonly string[]
  source_config_key?: string
  store_at?: string
}

/** Typed config param with UI hint. */
export interface NodeParamSpec {
  name: string
  type:
    | 'string'
    | 'integer'
    | 'number'
    | 'boolean'
    | 'enum'
    | 'string_list'
    | 'object'
    | 'array'
    | 'input_ref'
    | 'code'
  description: string
  required: boolean
  widget:
    | 'text'
    | 'textarea'
    | 'number'
    | 'checkbox'
    | 'select'
    | 'chips'
    | 'json'
    | 'input_ref'
    | 'code'
  default?: unknown
  enum?: readonly string[]
}

export interface NodeTypedSpec {
  inputPorts: readonly NodePortSpec[]
  outputPorts: readonly NodePortSpec[]
  params: readonly NodeParamSpec[]
}

export const NODE_TYPED: Record<NodeType, NodeTypedSpec> = {
  AGGREGATE: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to aggregate", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Aggregated results", "optional": false}] as const,
    params: [{"name": "group_by", "type": "array", "description": "Fields to group by", "required": false, "widget": "json", "default": []}, {"name": "aggregations", "type": "array", "description": "Aggregation operations", "required": true, "widget": "json", "default": []}] as const,
  },
  CODE: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to process", "optional": true}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Processed items", "optional": false}] as const,
    params: [{"name": "code", "type": "code", "description": "Python code to execute. Access items via 'items' variable", "required": true, "widget": "code", "default": "# Access input items\n# items = input['items']\n# Process and return\nreturn items"}, {"name": "mode", "type": "string", "description": "Execution mode", "required": false, "widget": "text", "default": "run_once_for_all", "enum": ["run_once_for_all", "run_once_for_each"]}] as const,
  },
  EXECUTE_WORKFLOW: {
    inputPorts: [{"name": "input", "type": "object", "description": "Data to pass to sub-workflow", "optional": true}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Sub-workflow output", "optional": false}] as const,
    params: [{"name": "workflow_id", "type": "string", "description": "ID of workflow to execute", "required": true, "widget": "text"}, {"name": "wait_for_completion", "type": "boolean", "description": "Wait for sub-workflow to complete", "required": false, "widget": "checkbox", "default": true}] as const,
  },
  FILTER: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to filter", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Filtered items", "optional": false}] as const,
    params: [{"name": "conditions", "type": "array", "description": "Filter conditions", "required": true, "widget": "json", "default": []}, {"name": "combine_operation", "type": "string", "description": "How to combine multiple conditions", "required": false, "widget": "text", "default": "AND", "enum": ["AND", "OR"]}] as const,
  },
  HTML_EXTRACT: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items containing HTML", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Extracted data", "optional": false}] as const,
    params: [{"name": "source_field", "type": "string", "description": "Field containing HTML", "required": false, "widget": "text", "default": "html"}, {"name": "extraction_values", "type": "array", "description": "Values to extract", "required": true, "widget": "json", "default": []}] as const,
  },
  HTTP_REQUEST: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to process", "optional": true}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "HTTP response data", "optional": false}] as const,
    params: [{"name": "method", "type": "string", "description": "HTTP method", "required": true, "widget": "text", "default": "GET", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]}, {"name": "url", "type": "string", "description": "URL to request", "required": true, "widget": "text"}, {"name": "headers", "type": "object", "description": "HTTP headers", "required": false, "widget": "json", "default": {}}, {"name": "body", "type": "object", "description": "Request body (for POST/PUT/PATCH)", "required": false, "widget": "json", "default": {}}, {"name": "options", "type": "object", "description": "", "required": false, "widget": "json", "default": {}}] as const,
  },
  IF: {
    inputPorts: [{"name": "input", "type": "object", "description": "Input items to evaluate against conditions", "optional": false}] as const,
    outputPorts: [{"name": true, "type": "object", "description": "Items that match the conditions", "optional": false}, {"name": false, "type": "object", "description": "Items that do not match the conditions", "optional": false}] as const,
    params: [{"name": "conditions", "type": "array", "description": "List of comparison conditions to evaluate", "required": true, "widget": "json", "default": []}, {"name": "combine_operation", "type": "string", "description": "How to combine multiple conditions", "required": false, "widget": "text", "default": "AND", "enum": ["AND", "OR"]}, {"name": "options", "type": "object", "description": "Additional options", "required": false, "widget": "json", "default": {}}] as const,
  },
  ITEM_LISTS: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to process", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Processed items", "optional": false}] as const,
    params: [{"name": "operation", "type": "string", "description": "Array operation to perform", "required": true, "widget": "text", "default": "split", "enum": ["split", "sort_array", "unique", "remove_duplicates", "flatten", "reverse", "shuffle"]}, {"name": "field_name", "type": "string", "description": "Field containing the array", "required": false, "widget": "text"}, {"name": "options", "type": "object", "description": "", "required": false, "widget": "json", "default": {}}] as const,
  },
  JSON: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to process", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Processed JSON data", "optional": false}] as const,
    params: [{"name": "operation", "type": "string", "description": "JSON operation", "required": true, "widget": "text", "default": "parse", "enum": ["parse", "stringify", "extract"]}, {"name": "field_name", "type": "string", "description": "Field containing JSON string (for parse)", "required": false, "widget": "text"}, {"name": "json_path", "type": "string", "description": "Path to extract (dot notation)", "required": false, "widget": "text"}] as const,
  },
  LIMIT: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to limit", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Limited items", "optional": false}] as const,
    params: [{"name": "max_items", "type": "integer", "description": "Maximum number of items to output", "required": true, "widget": "number", "default": 1}, {"name": "keep", "type": "string", "description": "Which items to keep", "required": false, "widget": "text", "default": "first", "enum": ["first", "last"]}] as const,
  },
  LOOP_OVER_ITEMS: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to loop over", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Current item", "optional": false}] as const,
    params: [{"name": "batch_size", "type": "integer", "description": "Number of items to process together", "required": false, "widget": "number", "default": 1}] as const,
  },
  MERGE: {
    inputPorts: [{"name": "input1", "type": "object", "description": "First input data stream", "optional": false}, {"name": "input2", "type": "object", "description": "Second input data stream", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Merged data", "optional": false}] as const,
    params: [{"name": "mode", "type": "string", "description": "How to merge the data", "required": true, "widget": "text", "default": "append", "enum": ["append", "combine", "choose_branch"]}, {"name": "combine_by", "type": "string", "description": "How to combine when mode=combine", "required": false, "widget": "text", "default": "matching_fields", "enum": ["matching_fields", "position", "all_combinations"]}, {"name": "fields_to_match", "type": "array", "description": "Field names to match on (for matching_fields mode)", "required": false, "widget": "json", "default": []}, {"name": "output_type", "type": "string", "description": "What to keep when combining", "required": false, "widget": "text", "default": "keep_matches", "enum": ["keep_matches", "keep_non_matches", "keep_everything", "enrich_input1", "enrich_input2"]}, {"name": "clash_handling", "type": "string", "description": "Which input to prioritize on field clash", "required": false, "widget": "text", "default": "prefer_input2", "enum": ["prefer_input1", "prefer_input2", "add_input_number"]}] as const,
  },
  SCHEDULE_TRIGGER: {
    inputPorts: [] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Trigger data with timestamp", "optional": false}] as const,
    params: [{"name": "mode", "type": "string", "description": "Schedule mode", "required": true, "widget": "text", "default": "interval", "enum": ["interval", "cron"]}, {"name": "interval", "type": "integer", "description": "Interval in minutes (interval mode)", "required": false, "widget": "number", "default": 60}, {"name": "cron_expression", "type": "string", "description": "Cron expression (cron mode)", "required": false, "widget": "text"}] as const,
  },
  SET: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to transform", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Transformed items", "optional": false}] as const,
    params: [{"name": "mode", "type": "string", "description": "How to set fields", "required": true, "widget": "text", "default": "manual", "enum": ["manual", "json"]}, {"name": "fields", "type": "array", "description": "Fields to set (manual mode)", "required": false, "widget": "json", "default": []}, {"name": "json_data", "type": "object", "description": "JSON object to merge (json mode)", "required": false, "widget": "json", "default": {}}, {"name": "options", "type": "object", "description": "Additional options", "required": false, "widget": "json", "default": {}}] as const,
  },
  SORT: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to sort", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Sorted items", "optional": false}] as const,
    params: [{"name": "sort_by", "type": "array", "description": "Fields to sort by", "required": true, "widget": "json", "default": []}, {"name": "options", "type": "object", "description": "", "required": false, "widget": "json", "default": {}}] as const,
  },
  SPLIT_IN_BATCHES: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to batch", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Batch of items", "optional": false}] as const,
    params: [{"name": "batch_size", "type": "integer", "description": "Number of items per batch", "required": true, "widget": "number", "default": 10}, {"name": "options", "type": "object", "description": "", "required": false, "widget": "json", "default": {}}] as const,
  },
  SPREADSHEET_FILE: {
    inputPorts: [{"name": "input", "type": "object", "description": "Data to write (for write operation)", "optional": true}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "File data", "optional": false}] as const,
    params: [{"name": "operation", "type": "string", "description": "File operation", "required": true, "widget": "text", "default": "read", "enum": ["read", "write"]}, {"name": "file_format", "type": "string", "description": "File format", "required": true, "widget": "text", "default": "csv", "enum": ["csv", "xlsx", "json"]}, {"name": "file_path", "type": "string", "description": "Path to file", "required": false, "widget": "text"}, {"name": "options", "type": "object", "description": "", "required": false, "widget": "json", "default": {}}] as const,
  },
  SWITCH: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to route", "optional": false}] as const,
    outputPorts: [{"name": "output0", "type": "object", "description": "Output 0", "optional": false}, {"name": "output1", "type": "object", "description": "Output 1", "optional": false}, {"name": "output2", "type": "object", "description": "Output 2", "optional": false}, {"name": "output3", "type": "object", "description": "Output 3", "optional": false}] as const,
    params: [{"name": "mode", "type": "string", "description": "Routing mode", "required": true, "widget": "text", "default": "rules", "enum": ["rules", "expression"]}, {"name": "rules", "type": "array", "description": "Routing rules (rules mode)", "required": false, "widget": "json", "default": []}, {"name": "fallback_output", "type": "integer", "description": "Output index for items that don't match any rule", "required": false, "widget": "number", "default": 0}] as const,
  },
  WAIT: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to pass through after waiting", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Items (unchanged)", "optional": false}] as const,
    params: [{"name": "amount", "type": "integer", "description": "Amount of time to wait", "required": true, "widget": "number", "default": 1}, {"name": "unit", "type": "string", "description": "Time unit", "required": true, "widget": "text", "default": "seconds", "enum": ["seconds", "minutes", "hours"]}] as const,
  },
  WEBHOOK: {
    inputPorts: [] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Webhook payload", "optional": false}] as const,
    params: [{"name": "path", "type": "string", "description": "Webhook path (auto-generated if empty)", "required": false, "widget": "text"}, {"name": "method", "type": "string", "description": "HTTP method to accept", "required": false, "widget": "text", "default": "POST", "enum": ["GET", "POST", "PUT", "DELETE", "ANY"]}, {"name": "response_mode", "type": "string", "description": "How to respond to webhook", "required": false, "widget": "text", "default": "on_received", "enum": ["on_received", "last_node", "response_node"]}] as const,
  },
  XML: {
    inputPorts: [{"name": "input", "type": "object", "description": "Items to process", "optional": false}] as const,
    outputPorts: [{"name": "output", "type": "object", "description": "Processed XML data", "optional": false}] as const,
    params: [{"name": "operation", "type": "string", "description": "XML operation", "required": true, "widget": "text", "default": "parse", "enum": ["parse", "stringify", "extract"]}, {"name": "field_name", "type": "string", "description": "Field containing XML string", "required": false, "widget": "text"}, {"name": "xpath", "type": "string", "description": "XPath to extract", "required": false, "widget": "text"}] as const,
  },
}

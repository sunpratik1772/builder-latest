"""
Canonical :func:`NodeSpec.type_id` strings for engine topology and hard-rules.

**AUTO-GENERATED** — run ``python backend/scripts/gen_artifacts.py``.
The canonical set is :data:`engine.registry.NODE_SPECS` keys; import from here
instead of string literals. Do not edit by hand.
"""
from __future__ import annotations

ACTIVATION_TRIGGER = "ACTIVATION_TRIGGER"
AGGREGATE = "AGGREGATE"
AI_TRANSFORM = "AI_TRANSFORM"
CHAT = "CHAT"
CHAT_TRIGGER = "CHAT_TRIGGER"
CODE = "CODE"
COMPARE_DATASETS = "COMPARE_DATASETS"
COMPRESSION = "COMPRESSION"
CONVERT_TO_FILE = "CONVERT_TO_FILE"
DATA_TABLE = "DATA_TABLE"
DATETIME = "DATETIME"
DATE_TIME = "DATE_TIME"
DB_MARKET_CONNECTOR = "DB_MARKET_CONNECTOR"
DB_SOLR_CONNECTOR = "DB_SOLR_CONNECTOR"
DEBUG_HELPER = "DEBUG_HELPER"
EDIT_IMAGE = "EDIT_IMAGE"
EMAIL_TRIGGER_IMAP = "EMAIL_TRIGGER_IMAP"
ERROR_TRIGGER = "ERROR_TRIGGER"
EVALUATION = "EVALUATION"
EVALUATION_TRIGGER = "EVALUATION_TRIGGER"
EXECUTE_COMMAND = "EXECUTE_COMMAND"
EXECUTE_WORKFLOW = "EXECUTE_WORKFLOW"
EXECUTE_WORKFLOW_TRIGGER = "EXECUTE_WORKFLOW_TRIGGER"
EXECUTION_DATA = "EXECUTION_DATA"
EXTRACT_FROM_FILE = "EXTRACT_FROM_FILE"
FAN_OUT = "FAN_OUT"
FILTER = "FILTER"
FTP = "FTP"
GIT = "GIT"
GRAPHQL = "GRAPHQL"
GUARDRAILS = "GUARDRAILS"
HTML = "HTML"
HTTP_REQUEST = "HTTP_REQUEST"
IF = "IF"
JWT = "JWT"
LDAP = "LDAP"
LIMIT = "LIMIT"
LLM_BASIC = "LLM_BASIC"
LOCAL_FILE_TRIGGER = "LOCAL_FILE_TRIGGER"
LOOP_OVER_ITEMS = "LOOP_OVER_ITEMS"
MANUAL_TRIGGER = "MANUAL_TRIGGER"
MARKDOWN = "MARKDOWN"
MARKET_API_CONNECTOR = "MARKET_API_CONNECTOR"
MCP_CLIENT = "MCP_CLIENT"
MCP_SERVER_TRIGGER = "MCP_SERVER_TRIGGER"
MERGE = "MERGE"
N8N_FORM = "N8N_FORM"
NO_OP = "NO_OP"
READ_WRITE_FILES_FROM_DISK = "READ_WRITE_FILES_FROM_DISK"
REMOVE_DUPLICATES = "REMOVE_DUPLICATES"
RENAME_KEYS = "RENAME_KEYS"
RESPOND_TO_WEBHOOK = "RESPOND_TO_WEBHOOK"
RESPONSE = "RESPONSE"
RSS_FEED_READ = "RSS_FEED_READ"
RSS_FEED_TRIGGER = "RSS_FEED_TRIGGER"
RSS_READ = "RSS_READ"
SCHEDULE_TRIGGER = "SCHEDULE_TRIGGER"
SEND_EMAIL = "SEND_EMAIL"
SET = "SET"
SORT = "SORT"
SPLIT_IN_BATCHES = "SPLIT_IN_BATCHES"
SPLIT_OUT = "SPLIT_OUT"
SPREADSHEET_FILE = "SPREADSHEET_FILE"
SSE_TRIGGER = "SSE_TRIGGER"
SSH = "SSH"
STOP_AND_ERROR = "STOP_AND_ERROR"
SUMMARIZE = "SUMMARIZE"
SWITCH = "SWITCH"
TAB_SUMMARY = "TAB_SUMMARY"
TOTP = "TOTP"
WAIT = "WAIT"
WEBHOOK = "WEBHOOK"
WHATSAPP = "WHATSAPP"
WORKFLOW_CONTEXT = "WORKFLOW_CONTEXT"
WORKFLOW_TRIGGER = "WORKFLOW_TRIGGER"
XML = "XML"
agent = "agent"
api_trigger = "api_trigger"
code = "code"
condition = "condition"
csv_extract = "csv_extract"
csv_output = "csv_output"
data_merge = "data_merge"
db_query = "db_query"
deduplicate = "deduplicate"
evaluator = "evaluator"
excel_output = "excel_output"
filter = "filter"
function = "function"
github = "github"
gmail = "gmail"
group_by = "group_by"
http = "http"
join = "join"
loop = "loop"
manual_trigger = "manual_trigger"
map_transform = "map_transform"
mcp = "mcp"
note = "note"
notion = "notion"
pause = "pause"
pdf_extract = "pdf_extract"
response = "response"
router = "router"
schedule = "schedule"
select_columns = "select_columns"
slack = "slack"
sort = "sort"
telegram = "telegram"
webhook_trigger = "webhook_trigger"

__all__ = [
    "ACTIVATION_TRIGGER",
    "AGGREGATE",
    "AI_TRANSFORM",
    "CHAT",
    "CHAT_TRIGGER",
    "CODE",
    "COMPARE_DATASETS",
    "COMPRESSION",
    "CONVERT_TO_FILE",
    "DATA_TABLE",
    "DATETIME",
    "DATE_TIME",
    "DB_MARKET_CONNECTOR",
    "DB_SOLR_CONNECTOR",
    "DEBUG_HELPER",
    "EDIT_IMAGE",
    "EMAIL_TRIGGER_IMAP",
    "ERROR_TRIGGER",
    "EVALUATION",
    "EVALUATION_TRIGGER",
    "EXECUTE_COMMAND",
    "EXECUTE_WORKFLOW",
    "EXECUTE_WORKFLOW_TRIGGER",
    "EXECUTION_DATA",
    "EXTRACT_FROM_FILE",
    "FAN_OUT",
    "FILTER",
    "FTP",
    "GIT",
    "GRAPHQL",
    "GUARDRAILS",
    "HTML",
    "HTTP_REQUEST",
    "IF",
    "JWT",
    "LDAP",
    "LIMIT",
    "LLM_BASIC",
    "LOCAL_FILE_TRIGGER",
    "LOOP_OVER_ITEMS",
    "MANUAL_TRIGGER",
    "MARKDOWN",
    "MARKET_API_CONNECTOR",
    "MCP_CLIENT",
    "MCP_SERVER_TRIGGER",
    "MERGE",
    "N8N_FORM",
    "NO_OP",
    "READ_WRITE_FILES_FROM_DISK",
    "REMOVE_DUPLICATES",
    "RENAME_KEYS",
    "RESPOND_TO_WEBHOOK",
    "RESPONSE",
    "RSS_FEED_READ",
    "RSS_FEED_TRIGGER",
    "RSS_READ",
    "SCHEDULE_TRIGGER",
    "SEND_EMAIL",
    "SET",
    "SORT",
    "SPLIT_IN_BATCHES",
    "SPLIT_OUT",
    "SPREADSHEET_FILE",
    "SSE_TRIGGER",
    "SSH",
    "STOP_AND_ERROR",
    "SUMMARIZE",
    "SWITCH",
    "TAB_SUMMARY",
    "TOTP",
    "WAIT",
    "WEBHOOK",
    "WHATSAPP",
    "WORKFLOW_CONTEXT",
    "WORKFLOW_TRIGGER",
    "XML",
    "agent",
    "api_trigger",
    "code",
    "condition",
    "csv_extract",
    "csv_output",
    "data_merge",
    "db_query",
    "deduplicate",
    "evaluator",
    "excel_output",
    "filter",
    "function",
    "github",
    "gmail",
    "group_by",
    "http",
    "join",
    "loop",
    "manual_trigger",
    "map_transform",
    "mcp",
    "note",
    "notion",
    "pause",
    "pdf_extract",
    "response",
    "router",
    "schedule",
    "select_columns",
    "slack",
    "sort",
    "telegram",
    "webhook_trigger",
]

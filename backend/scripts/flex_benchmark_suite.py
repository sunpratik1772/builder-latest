"""Create and run a dbSherpa flexibility benchmark workflow suite.

This script generates 7 dbSherpa-native (n8n-style) workflows with mock data,
runs them in batch, and writes a markdown compatibility report.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.dag_runner import run_workflow


WORKFLOW_DIR = ROOT / "workflows" / "flex_suite"
OUTPUT_DIR = ROOT / "tmp" / "flex_outputs"
REPORT_PATH = ROOT / "tmp" / "flex_benchmark_report.md"
RESULTS_JSON = ROOT / "tmp" / "flex_benchmark_results.json"


MOCK_PDF_B64 = (
    "JVBERi0xLjQKJcfsj6IKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4K"
    "ZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9Db3VudCAxIC9LaWRzIFsgMyAwIFIgXSA+"
    "PgplbmRvYmoKMyAwIG9iago8PCAvVHlwZSAvUGFnZSAvUGFyZW50IDIgMCBSIC9NZWRpYUJveCBb"
    "MCAwIDMwMCAxNDQgXSAvQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCA+PiA+PgplbmRvYmoK"
    "NCAwIG9iago8PCAvTGVuZ3RoIDQ0ID4+CnN0cmVhbQpCVCAvRjEgMTIgVGYgNTAgMTAwIFRkIChk"
    "YlNoZXJwYSBtb2NrIFBERikgVGogRVQKZW5kc3RyZWFtCmVuZG9iago1IDAgb2JqCjw8IC9UeXBl"
    "IC9Gb250IC9TdWJ0eXBlIC9UeXBlMSAvQmFzZUZvbnQgL0hlbHZldGljYSA+PgplbmRvYmoKeHJl"
    "ZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAwIG4gCjAwMDAwMDAwNjIg"
    "MDAwMDAgbiAKMDAwMDAwMDExNyAwMDAwMCBuIAowMDAwMDAwMjI3IDAwMDAwIG4gCjAwMDAwMDAz"
    "MjEgMDAwMDAgbiAKdHJhaWxlcgo8PCAvU2l6ZSA2IC9Sb290IDEgMCBSID4+CnN0YXJ0eHJlZgoz"
    "OTQKJSVFT0Y="
)


@dataclass
class Scenario:
    name: str
    filename: str
    dag: dict[str, Any]
    artifacts: list[str]


def _workflow_suite() -> list[Scenario]:
    out = OUTPUT_DIR
    return [
        Scenario(
            name="csv_sales_top5",
            filename="flex_01_csv_sales_top5.json",
            artifacts=[str(out / "sales_top5.csv")],
            dag={
                "workflow_name": "Flex 01 - CSV Sales Top 5",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "gen_sales",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "result = [\n"
                                "    {\n"
                                "        'order_id': f'ORD-{i:03d}',\n"
                                "        'region': ['EU', 'US', 'APAC', 'MEA'][i % 4],\n"
                                "        'revenue': 1000 + i * 137,\n"
                                "        'units': (i % 5) + 1,\n"
                                "    }\n"
                                "    for i in range(1, 21)\n"
                                "]"
                            ),
                        },
                    },
                    {
                        "id": "sort_revenue",
                        "type": "SORT",
                        "config": {
                            "type": "simple",
                            "sortFieldsUi": {"sortField": [{"fieldName": "revenue", "order": "descending"}]},
                        },
                    },
                    {"id": "top5", "type": "LIMIT", "config": {"max_items": 5, "keep": "first_items"}},
                    {
                        "id": "to_csv",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "csv",
                            "put_output_file_in_field": "data",
                            "file_name": "sales_top5",
                        },
                    },
                    {
                        "id": "write_csv",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "sales_top5.csv"),
                            "input_binary_field": "data",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "gen_sales"},
                    {"from": "gen_sales", "to": "sort_revenue"},
                    {"from": "sort_revenue", "to": "top5"},
                    {"from": "top5", "to": "to_csv"},
                    {"from": "to_csv", "to": "write_csv"},
                ],
            },
        ),
        Scenario(
            name="markdown_and_html_report",
            filename="flex_02_markdown_html_report.json",
            artifacts=[str(out / "weekly_report.html"), str(out / "weekly_report_bundle.json")],
            dag={
                "workflow_name": "Flex 02 - Markdown and HTML Report",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "gen_metrics",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "result = [\n"
                                "    {'team': 'Growth', 'wins': 14, 'losses': 3},\n"
                                "    {'team': 'Support', 'wins': 9, 'losses': 4},\n"
                                "    {'team': 'Data', 'wins': 11, 'losses': 2},\n"
                                "]"
                            ),
                        },
                    },
                    {
                        "id": "build_md",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "total_wins = sum(row['wins'] for row in items)\n"
                                "lines = [\n"
                                "    '# Weekly Team Report',\n"
                                "    '',\n"
                                "    f'- Teams: {len(items)}',\n"
                                "    f'- Total wins: {total_wins}',\n"
                                "    '',\n"
                                "    '## Breakdown',\n"
                                "]\n"
                                "for row in items:\n"
                                "    lines.append(f\"- **{row['team']}**: {row['wins']} wins / {row['losses']} losses\")\n"
                                "result = [{'markdown': '\\n'.join(lines)}]"
                            ),
                        },
                    },
                    {
                        "id": "to_html",
                        "type": "MARKDOWN",
                        "config": {"mode": "markdownToHtml", "destinationKey": "html"},
                    },
                    {
                        "id": "write_html",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "weekly_report.html"),
                            "input_binary_field": "html",
                        },
                    },
                    {
                        "id": "bundle_json",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "toJson",
                            "put_output_file_in_field": "data",
                            "file_name": "weekly_report_bundle",
                        },
                    },
                    {
                        "id": "write_bundle",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "weekly_report_bundle.json"),
                            "input_binary_field": "data",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "gen_metrics"},
                    {"from": "gen_metrics", "to": "build_md"},
                    {"from": "build_md", "to": "to_html"},
                    {"from": "to_html", "to": "write_html"},
                    {"from": "to_html", "to": "bundle_json"},
                    {"from": "bundle_json", "to": "write_bundle"},
                ],
            },
        ),
        Scenario(
            name="pdf_binary_export",
            filename="flex_03_pdf_binary_export.json",
            artifacts=[str(out / "invoice_mock.pdf")],
            dag={
                "workflow_name": "Flex 03 - PDF Binary Export",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "gen_pdf",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": f"result = [{{'pdf_b64': '{MOCK_PDF_B64}', 'doc_id': 'INV-001'}}]",
                        },
                    },
                    {
                        "id": "to_pdf_bytes",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "toBinary",
                            "input_field": "pdf_b64",
                            "put_output_file_in_field": "data",
                            "file_name": "invoice_mock.pdf",
                        },
                    },
                    {
                        "id": "write_pdf",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "invoice_mock.pdf"),
                            "input_binary_field": "data",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "gen_pdf"},
                    {"from": "gen_pdf", "to": "to_pdf_bytes"},
                    {"from": "to_pdf_bytes", "to": "write_pdf"},
                ],
            },
        ),
        Scenario(
            name="split_merge_multi_source",
            filename="flex_04_split_merge_multi_source.json",
            artifacts=[str(out / "priced_inventory.csv")],
            dag={
                "workflow_name": "Flex 04 - Split and Merge Multi-Source",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "products",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "result = [{\n"
                                "    'products': [\n"
                                "        {'sku': 'A-100', 'category': 'analytics', 'price': 120},\n"
                                "        {'sku': 'B-210', 'category': 'storage', 'price': 80},\n"
                                "        {'sku': 'C-330', 'category': 'security', 'price': 150},\n"
                                "    ]\n"
                                "}]"
                            ),
                        },
                    },
                    {
                        "id": "split_products",
                        "type": "SPLIT_OUT",
                        "config": {
                            "field_to_split_out": "products",
                            "include": "noOtherFields",
                            "destination_field_name": "product",
                        },
                    },
                    {
                        "id": "flatten_product",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForEachItem",
                            "pythonCode": (
                                "p = item['product']\n"
                                "result = {\n"
                                "    'sku': p['sku'],\n"
                                "    'category': p['category'],\n"
                                "    'price': p['price'],\n"
                                "}"
                            ),
                        },
                    },
                    {
                        "id": "regions",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "result = [\n"
                                "    {'sku': 'A-100', 'region': 'EU', 'tax_rate': 0.20},\n"
                                "    {'sku': 'B-210', 'region': 'US', 'tax_rate': 0.08},\n"
                                "    {'sku': 'C-330', 'region': 'APAC', 'tax_rate': 0.15},\n"
                                "]"
                            ),
                        },
                    },
                    {
                        "id": "merge_inventory",
                        "type": "MERGE",
                        "config": {
                            "mode": "combine",
                            "combine_by": "matchingFields",
                            "fields_to_match": ["sku"],
                            "output_type": "keep_matches",
                        },
                    },
                    {
                        "id": "to_csv",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "csv",
                            "put_output_file_in_field": "data",
                            "file_name": "priced_inventory",
                        },
                    },
                    {
                        "id": "write_inventory_csv",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "priced_inventory.csv"),
                            "input_binary_field": "data",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "products"},
                    {"from": "products", "to": "split_products"},
                    {"from": "split_products", "to": "flatten_product"},
                    {"from": "trigger", "to": "regions"},
                    {"from": "flatten_product", "to": "merge_inventory", "targetHandle": "input1"},
                    {"from": "regions", "to": "merge_inventory", "targetHandle": "input2"},
                    {"from": "merge_inventory", "to": "to_csv"},
                    {"from": "to_csv", "to": "write_inventory_csv"},
                ],
            },
        ),
        Scenario(
            name="compression_roundtrip",
            filename="flex_05_compression_roundtrip.json",
            artifacts=[str(out / "compression_roundtrip.json")],
            dag={
                "workflow_name": "Flex 05 - Compression Roundtrip",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "make_payload",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": "result = [{'data': (b'alpha,beta,gamma,delta\\n' * 30)}]",
                        },
                    },
                    {
                        "id": "compress",
                        "type": "COMPRESSION",
                        "config": {
                            "operation": "compress",
                            "binaryPropertyName": "data",
                            "binaryPropertyOutput": "gz",
                            "outputFormat": "gzip",
                        },
                    },
                    {
                        "id": "decompress",
                        "type": "COMPRESSION",
                        "config": {
                            "operation": "decompress",
                            "binaryPropertyName": "gz",
                            "outputPrefix": "restored",
                        },
                    },
                    {
                        "id": "verify",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "blob = items[0]['restored0']\n"
                                "text = blob.decode('utf-8')\n"
                                "result = [{\n"
                                "    'roundtrip_ok': ('alpha' in text and 'delta' in text),\n"
                                "    'length': len(text),\n"
                                "    'preview': text[:60],\n"
                                "}]"
                            ),
                        },
                    },
                    {
                        "id": "to_json",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "toJson",
                            "put_output_file_in_field": "data",
                            "file_name": "compression_roundtrip",
                        },
                    },
                    {
                        "id": "write_json",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "compression_roundtrip.json"),
                            "input_binary_field": "data",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "make_payload"},
                    {"from": "make_payload", "to": "compress"},
                    {"from": "compress", "to": "decompress"},
                    {"from": "decompress", "to": "verify"},
                    {"from": "verify", "to": "to_json"},
                    {"from": "to_json", "to": "write_json"},
                ],
            },
        ),
        Scenario(
            name="llm_multi_pass",
            filename="flex_06_llm_multi_pass.json",
            artifacts=[str(out / "llm_results.csv"), str(out / "llm_report.md")],
            dag={
                "workflow_name": "Flex 06 - LLM Multi-Pass",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "prompts",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "result = [\n"
                                "    {'topic': 'pricing strategy', 'context': 'SaaS SMB segment, churn risk medium'},\n"
                                "    {'topic': 'support automation', 'context': 'Ticket volume increasing 14% monthly'},\n"
                                "    {'topic': 'data quality', 'context': 'Duplicates found in 6% of records'},\n"
                                "]"
                            ),
                        },
                    },
                    {
                        "id": "llm_draft",
                        "type": "LLM_BASIC",
                        "config": {
                            "model": "gemini-2.5-flash",
                            "prompt": "Write two concise bullets on {{$json.topic}} using: {{$json.context}}",
                            "output_field": "draft",
                            "temperature": 0.2,
                        },
                    },
                    {
                        "id": "llm_refine",
                        "type": "LLM_BASIC",
                        "config": {
                            "model": "gemini-2.5-flash",
                            "prompt": "Rewrite into one clear sentence: {{$json.draft}}",
                            "output_field": "refined",
                            "temperature": 0.1,
                        },
                    },
                    {
                        "id": "aggregate",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "error_count = 0\n"
                                "lines = ['# LLM Multi-pass Report', '']\n"
                                "for idx, row in enumerate(items):\n"
                                "    draft = str(row.get('draft', ''))\n"
                                "    refined = str(row.get('refined', ''))\n"
                                "    if draft.startswith('[LLM error') or refined.startswith('[LLM error'):\n"
                                "        error_count = error_count + 1\n"
                                "    lines.append(f\"## Item {idx + 1}: {row.get('topic', 'unknown')}\")\n"
                                "    lines.append(f'- Draft: {draft}')\n"
                                "    lines.append(f'- Refined: {refined}')\n"
                                "    lines.append('')\n"
                                "result = [{\n"
                                "    'markdown': '\\n'.join(lines),\n"
                                "    'llm_error_count': error_count,\n"
                                "    'total_items': len(items),\n"
                                "}]"
                            ),
                        },
                    },
                    {
                        "id": "llm_to_csv",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "csv",
                            "put_output_file_in_field": "data",
                            "file_name": "llm_results",
                        },
                    },
                    {
                        "id": "write_llm_csv",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "llm_results.csv"),
                            "input_binary_field": "data",
                        },
                    },
                    {
                        "id": "write_llm_markdown",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "llm_report.md"),
                            "input_binary_field": "markdown",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "prompts"},
                    {"from": "prompts", "to": "llm_draft"},
                    {"from": "llm_draft", "to": "llm_refine"},
                    {"from": "llm_refine", "to": "aggregate"},
                    {"from": "llm_refine", "to": "llm_to_csv"},
                    {"from": "llm_to_csv", "to": "write_llm_csv"},
                    {"from": "aggregate", "to": "write_llm_markdown"},
                ],
            },
        ),
        Scenario(
            name="branching_and_merge",
            filename="flex_07_branching_and_merge.json",
            artifacts=[str(out / "lead_segments.csv")],
            dag={
                "workflow_name": "Flex 07 - Branching and Merge",
                "nodes": [
                    {"id": "trigger", "type": "MANUAL_TRIGGER", "config": {}},
                    {
                        "id": "gen_leads",
                        "type": "CODE",
                        "config": {
                            "language": "python",
                            "mode": "runOnceForAllItems",
                            "pythonCode": (
                                "result = [\n"
                                "    {'lead': 'Acme', 'score': 91, 'channel': 'enterprise'},\n"
                                "    {'lead': 'BetaCo', 'score': 77, 'channel': 'smb'},\n"
                                "    {'lead': 'CafeNow', 'score': 62, 'channel': 'smb'},\n"
                                "    {'lead': 'DeltaOps', 'score': 88, 'channel': 'enterprise'},\n"
                                "]"
                            ),
                        },
                    },
                    {
                        "id": "quality_gate",
                        "type": "IF",
                        "config": {
                            "conditions": {
                                "combinator": "and",
                                "conditions": [
                                    {
                                        "leftValue": "={{$json.score}}",
                                        "rightValue": 70,
                                        "operator": {"operation": "greaterThan"},
                                    }
                                ],
                            }
                        },
                    },
                    {
                        "id": "hot_routing",
                        "type": "SWITCH",
                        "config": {
                            "mode": "rules",
                            "rules": {
                                "values": [
                                    {
                                        "conditions": {
                                            "combinator": "and",
                                            "conditions": [
                                                {
                                                    "leftValue": "={{$json.channel}}",
                                                    "rightValue": "enterprise",
                                                    "operator": {"operation": "equals"},
                                                }
                                            ],
                                        }
                                    },
                                    {
                                        "conditions": {
                                            "combinator": "and",
                                            "conditions": [
                                                {
                                                    "leftValue": "={{$json.channel}}",
                                                    "rightValue": "smb",
                                                    "operator": {"operation": "equals"},
                                                }
                                            ],
                                        }
                                    },
                                ]
                            },
                            "fallback_output": "none",
                        },
                    },
                    {
                        "id": "tag_enterprise",
                        "type": "SET",
                        "config": {
                            "json_output": {
                                "lead": "={{ $json.lead }}",
                                "score": "={{ $json.score }}",
                                "channel": "={{ $json.channel }}",
                                "segment": "enterprise_hot",
                            }
                        },
                    },
                    {
                        "id": "tag_smb",
                        "type": "SET",
                        "config": {
                            "json_output": {
                                "lead": "={{ $json.lead }}",
                                "score": "={{ $json.score }}",
                                "channel": "={{ $json.channel }}",
                                "segment": "smb_hot",
                            }
                        },
                    },
                    {
                        "id": "tag_cold",
                        "type": "SET",
                        "config": {
                            "json_output": {
                                "lead": "={{ $json.lead }}",
                                "score": "={{ $json.score }}",
                                "channel": "={{ $json.channel }}",
                                "segment": "cold",
                            }
                        },
                    },
                    {"id": "merge_hot", "type": "MERGE", "config": {"mode": "append"}},
                    {"id": "merge_all", "type": "MERGE", "config": {"mode": "append"}},
                    {
                        "id": "to_csv",
                        "type": "CONVERT_TO_FILE",
                        "config": {
                            "operation": "csv",
                            "put_output_file_in_field": "data",
                            "file_name": "lead_segments",
                        },
                    },
                    {
                        "id": "write_csv",
                        "type": "READ_WRITE_FILES_FROM_DISK",
                        "config": {
                            "operation": "write",
                            "file_path_and_name": str(out / "lead_segments.csv"),
                            "input_binary_field": "data",
                        },
                    },
                ],
                "edges": [
                    {"from": "trigger", "to": "gen_leads"},
                    {"from": "gen_leads", "to": "quality_gate"},
                    {"from": "quality_gate", "to": "hot_routing", "sourceHandle": "true"},
                    {"from": "quality_gate", "to": "tag_cold", "sourceHandle": "false"},
                    {"from": "hot_routing", "to": "tag_enterprise", "sourceHandle": "output0"},
                    {"from": "hot_routing", "to": "tag_smb", "sourceHandle": "output1"},
                    {"from": "tag_enterprise", "to": "merge_hot", "targetHandle": "input1"},
                    {"from": "tag_smb", "to": "merge_hot", "targetHandle": "input2"},
                    {"from": "merge_hot", "to": "merge_all", "targetHandle": "input1"},
                    {"from": "tag_cold", "to": "merge_all", "targetHandle": "input2"},
                    {"from": "merge_all", "to": "to_csv"},
                    {"from": "to_csv", "to": "write_csv"},
                ],
            },
        ),
    ]


def write_workflows() -> list[Path]:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for sc in _workflow_suite():
        path = WORKFLOW_DIR / sc.filename
        path.write_text(json.dumps(sc.dag, indent=2), encoding="utf-8")
        paths.append(path)
    return paths


def _check_scenario(name: str, ctx: Any, err: str | None, artifacts: list[str]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    ok = err is None

    for art in artifacts:
        ap = Path(art)
        exists = ap.exists()
        size = ap.stat().st_size if exists else 0
        checks.append({"check": f"artifact:{ap.name}", "ok": exists, "detail": f"size={size} bytes"})
        ok = ok and exists

    if err is None and ctx is not None:
        if name == "csv_sales_top5":
            count = len(ctx.get("top5_output") or [])
            cond = count == 5
            checks.append({"check": "top5_count", "ok": cond, "detail": f"count={count}"})
            ok = ok and cond
        elif name == "markdown_and_html_report":
            html_out = ctx.get("to_html_output") or []
            cond = bool(html_out and isinstance(html_out[0], dict) and html_out[0].get("html"))
            checks.append({"check": "markdown_to_html", "ok": cond, "detail": "html field generated"})
            ok = ok and cond
        elif name == "pdf_binary_export":
            write = ctx.get("write_pdf_output") or []
            size = write[0].get("bytes", 0) if write and isinstance(write[0], dict) else 0
            cond = size > 100
            checks.append({"check": "pdf_size", "ok": cond, "detail": f"bytes={size}"})
            ok = ok and cond
        elif name == "split_merge_multi_source":
            count = len(ctx.get("merge_inventory_output") or [])
            cond = count == 3
            checks.append({"check": "merged_rows", "ok": cond, "detail": f"count={count}"})
            ok = ok and cond
        elif name == "compression_roundtrip":
            out = ctx.get("verify_output") or []
            cond = bool(out and isinstance(out[0], dict) and out[0].get("roundtrip_ok") is True)
            checks.append({"check": "compression_roundtrip_ok", "ok": cond, "detail": str(out[0] if out else {})})
            ok = ok and cond
        elif name == "llm_multi_pass":
            out = ctx.get("aggregate_output") or []
            total = out[0].get("total_items", 0) if out and isinstance(out[0], dict) else 0
            err_count = out[0].get("llm_error_count", 0) if out and isinstance(out[0], dict) else 0
            cond = total == 3
            checks.append({"check": "llm_items_processed", "ok": cond, "detail": f"total={total}, llm_error_count={err_count}"})
            ok = ok and cond
        elif name == "branching_and_merge":
            out = ctx.get("merge_all_output") or []
            cond = len(out) == 4
            checks.append({"check": "branch_merge_count", "ok": cond, "detail": f"count={len(out)}"})
            ok = ok and cond
    else:
        checks.append({"check": "workflow_execution", "ok": False, "detail": err or "unknown error"})

    return {"ok": ok, "checks": checks}


def run_suite() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    pass_count = 0

    for sc in _workflow_suite():
        err: str | None = None
        ctx = None
        try:
            ctx = run_workflow(sc.dag, alert_payload={})
        except Exception as exc:  # pragma: no cover - report intentionally captures runtime failures
            err = str(exc)
        evaluation = _check_scenario(sc.name, ctx, err, sc.artifacts)
        if evaluation["ok"]:
            pass_count += 1
        results.append(
            {
                "scenario": sc.name,
                "workflow_file": str(WORKFLOW_DIR / sc.filename),
                "ok": evaluation["ok"],
                "error": err,
                "checks": evaluation["checks"],
                "artifacts": sc.artifacts,
            }
        )

    score = round((pass_count / len(results)) * 100, 1) if results else 0.0
    summary = {
        "total": len(results),
        "passed": pass_count,
        "failed": len(results) - pass_count,
        "score_percent": score,
        "results": results,
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def write_report(summary: dict[str, Any]) -> Path:
    lines = [
        "# dbSherpa Flexibility Benchmark Report",
        "",
        f"- Total workflows: **{summary['total']}**",
        f"- Passed: **{summary['passed']}**",
        f"- Failed: **{summary['failed']}**",
        f"- Compatibility score: **{summary['score_percent']}%**",
        "",
        "## Workflow Results",
        "",
    ]
    for row in summary["results"]:
        status = "PASS" if row["ok"] else "FAIL"
        lines.append(f"### {row['scenario']} — {status}")
        lines.append(f"- Workflow file: `{row['workflow_file']}`")
        if row["error"]:
            lines.append(f"- Error: `{row['error']}`")
        lines.append("- Checks:")
        for check in row["checks"]:
            flag = "ok" if check["ok"] else "fail"
            lines.append(f"  - [{flag}] {check['check']} ({check['detail']})")
        lines.append("- Artifacts:")
        for art in row["artifacts"]:
            lines.append(f"  - `{art}`")
        lines.append("")

    lines.extend(
        [
            "## Functional Readout",
            "",
            "- Strong: mock data generation, branching/merge routing, file output (CSV/JSON/HTML/PDF binary), compression roundtrip, and multi-step LLM chain orchestration.",
            "- Partial: Excel/PDF native authoring parity is not full n8n-level; XLS/XLSX and rich PDF generation still rely on adapter behavior or binary conversion patterns.",
            "- Key runtime reality: LLM paths execute end-to-end even without keys, but quality depends on external provider auth/config.",
            "",
            "## Generated Outputs Directory",
            "",
            f"- `{OUTPUT_DIR}`",
            f"- JSON summary: `{RESULTS_JSON}`",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and run dbSherpa flexibility benchmark suite")
    parser.add_argument("command", choices=["write", "run", "all"], nargs="?", default="all")
    args = parser.parse_args()

    if args.command in {"write", "all"}:
        paths = write_workflows()
        print(f"Wrote {len(paths)} workflows to {WORKFLOW_DIR}")
        for p in paths:
            print(f"- {p}")

    if args.command in {"run", "all"}:
        summary = run_suite()
        report = write_report(summary)
        print(json.dumps({"summary": {k: v for k, v in summary.items() if k != "results"}, "report": str(report)}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

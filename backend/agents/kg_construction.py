"""
Knowledge Graph Construction engine — Lessons 8I & 8II.
Handles:
  1. Domain graph construction from CSV files (rule-based Cypher import)
  2. Subject/lexical graph construction from unstructured text (neo4j-graphrag SimpleKGPipeline)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from neo4j_client import graphdb, tool_success, tool_error
from config import get_settings


# ══════════════════════════════════════════════════════════
# 1.  Domain graph (structured CSV → Cypher)
# ══════════════════════════════════════════════════════════

def create_uniqueness_constraint(label: str, unique_property_key: str) -> dict[str, Any]:
    """Creates a Neo4j uniqueness constraint for a node label + property."""
    name = f"{label}_{unique_property_key}_constraint"
    query = f"""CREATE CONSTRAINT `{name}` IF NOT EXISTS
    FOR (n:`{label}`)
    REQUIRE n.`{unique_property_key}` IS UNIQUE"""
    return graphdb.send_query(query)


def load_nodes_from_csv(
    source_file: str,
    label: str,
    unique_column_name: str,
    properties: list[str],
) -> dict[str, Any]:
    """Batch loads nodes from a CSV file using LOAD CSV + MERGE."""
    query = f"""LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
    CALL (row) {{
        MERGE (n:$($label) {{ {unique_column_name} : row[$unique_column_name] }})
        FOREACH (k IN $properties | SET n[k] = row[k])
    }} IN TRANSACTIONS OF 1000 ROWS
    """
    return graphdb.send_query(query, {
        "source_file": source_file,
        "label": label,
        "unique_column_name": unique_column_name,
        "properties": properties,
    })


def import_nodes(node_construction: dict) -> dict[str, Any]:
    constraint = create_uniqueness_constraint(
        node_construction["label"],
        node_construction["unique_column_name"],
    )
    if constraint["status"] == "error":
        return constraint
    return load_nodes_from_csv(
        node_construction["source_file"],
        node_construction["label"],
        node_construction["unique_column_name"],
        node_construction["properties"],
    )


def import_relationships(rel_construction: dict) -> dict[str, Any]:
    from_col = rel_construction["from_node_column"]
    to_col = rel_construction["to_node_column"]
    query = f"""LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
    CALL (row) {{
        MATCH (from_node:$($from_node_label) {{ {from_col} : row[$from_node_column] }}),
              (to_node:$($to_node_label)   {{ {to_col}   : row[$to_node_column]   }} )
        MERGE (from_node)-[r:$($relationship_type)]->(to_node)
        FOREACH (k IN $properties | SET r[k] = row[k])
    }} IN TRANSACTIONS OF 1000 ROWS
    """
    return graphdb.send_query(query, {
        "source_file": rel_construction["source_file"],
        "from_node_label": rel_construction["from_node_label"],
        "from_node_column": from_col,
        "to_node_label": rel_construction["to_node_label"],
        "to_node_column": to_col,
        "relationship_type": rel_construction["relationship_type"],
        "properties": rel_construction["properties"],
    })


def construct_domain_graph(construction_plan: dict) -> dict[str, Any]:
    """Runs the full domain graph construction from a construction plan dict."""
    results: list[dict] = []

    # Phase 1: nodes first
    for rule in construction_plan.values():
        if rule.get("construction_type") == "node":
            results.append(import_nodes(rule))

    # Phase 2: relationships
    for rule in construction_plan.values():
        if rule.get("construction_type") == "relationship":
            results.append(import_relationships(rule))

    errors = [r for r in results if r.get("status") == "error"]
    if errors:
        return tool_error(f"Construction completed with {len(errors)} errors: {errors[:3]}")
    return tool_success("domain_graph_constructed", {"rules_executed": len(results)})


# ══════════════════════════════════════════════════════════
# 2.  Subject/lexical graph (unstructured markdown → KG pipeline)
# ══════════════════════════════════════════════════════════

class RegexTextSplitter:
    """Custom splitter that chunks markdown on '---' delimiters."""
    def __init__(self, pattern: str = "---"):
        self._pattern = pattern

    async def run(self, text: str):
        # Lazy import to avoid hard dependency if neo4j-graphrag not installed
        try:
            from neo4j_graphrag.experimental.components.types import TextChunk, TextChunks
        except ImportError:
            raise ImportError("Install neo4j-graphrag to use subject graph construction.")
        texts = re.split(self._pattern, text)
        chunks = [TextChunk(text=str(t), index=i) for i, t in enumerate(texts)]
        return TextChunks(chunks=chunks)


def _file_context(file_path: str, num_lines: int = 5) -> str:
    with open(file_path, "r", encoding="utf-8") as fh:
        return "\n".join(line for _, line in zip(range(num_lines), fh))


async def build_subject_graph(
    approved_files: list[str],
    approved_entities: list[str],
    approved_fact_types: dict,
) -> dict[str, Any]:
    """
    Builds the subject + lexical graph from markdown files using
    neo4j-graphrag SimpleKGPipeline.

    Args:
        approved_files: List of markdown file paths relative to data dir.
        approved_entities: List of entity type strings.
        approved_fact_types: Dict of fact triples (from Lesson 7).
    """
    try:
        from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
        from neo4j_graphrag.experimental.components.pdf_loader import DataLoader
        from neo4j_graphrag.experimental.components.types import PdfDocument, DocumentInfo
        from neo4j_graphrag.llm import OpenAILLM
        from neo4j_graphrag.embeddings import OpenAIEmbeddings
    except ImportError:
        return tool_error(
            "neo4j-graphrag is not installed. "
            "Run: pip install neo4j-graphrag"
        )

    cfg = get_settings()
    data_dir = Path(cfg.data_dir)

    llm_for_neo4j = OpenAILLM(model_name=cfg.openai_model, model_params={"temperature": 0})
    embedder = OpenAIEmbeddings(model=cfg.openai_embedding_model)
    driver = graphdb.get_driver()

    schema_relationship_types = [k.upper() for k in approved_fact_types.keys()]
    schema_patterns = [
        [f["subject_label"], f["predicate_label"].upper(), f["object_label"]]
        for f in approved_fact_types.values()
    ]
    entity_schema = {
        "node_types": approved_entities,
        "relationship_types": schema_relationship_types,
        "patterns": schema_patterns,
        "additional_node_types": False,
    }

    class MarkdownDataLoader(DataLoader):
        async def run(self, filepath, metadata=None):
            with open(filepath, "r") as f:
                text = f.read()
            match = re.search(r"^# (.+)$", text, re.MULTILINE)
            title = match.group(1) if match else "Untitled"
            return PdfDocument(
                text=text,
                document_info=DocumentInfo(path=str(filepath), metadata={"title": title}),
            )

    splitter = RegexTextSplitter("---")
    processed: list[str] = []

    for file_name in approved_files:
        file_path = data_dir / file_name
        if not file_path.exists():
            continue

        context = _file_context(str(file_path))
        prompt = f"""
        You are a top-tier algorithm for information extraction.
        Extract entities (nodes) and relationships from the text.
        Return JSON: {{"nodes": [...], "relationships": [...]}}
        Use only: {{schema}}
        Context about the document:
        <context>{context}</context>
        Input: {{text}}
        """

        pipeline = SimpleKGPipeline(
            llm=llm_for_neo4j,
            driver=driver,
            embedder=embedder,
            from_pdf=True,
            pdf_loader=MarkdownDataLoader(),
            text_splitter=splitter,
            schema=entity_schema,
            prompt_template=prompt,
        )
        await pipeline.run_async(file_path=str(file_path))
        processed.append(file_name)

    return tool_success("subject_graph_built", {"files_processed": processed})

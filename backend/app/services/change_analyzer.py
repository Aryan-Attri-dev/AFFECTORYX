import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.analysis import (
    ChangeSeverity,
    BreakingCategory,
    ChangeAnalysis,
)
from app.schemas.analysis import ChangeFinding
from app.services.ingestion.openapi_parser import OpenAPIParser


class ChangeAnalyzerService:
    @staticmethod
    def compare_openapi_specs(
        db: Session,
        organization_id: str,
        project_id: str,
        author_id: str,
        title: str,
        base_spec_str: str,
        target_spec_str: str,
        base_version: str = "v1.0.0",
        target_version: str = "v2.0.0",
    ) -> ChangeAnalysis:
        if len(base_spec_str) > 10 * 1024 * 1024 or len(target_spec_str) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="OpenAPI specification exceeds 10MB size limit")

        base_spec = OpenAPIParser.parse_content(base_spec_str)
        target_spec = OpenAPIParser.parse_content(target_spec_str)

        findings: List[Dict[str, Any]] = []

        base_paths = base_spec.get("paths", {})
        target_paths = target_spec.get("paths", {})

        valid_methods = {"get", "post", "put", "patch", "delete", "options", "head"}

        # 1. Compare Base vs Target (Detect removals, breaking alterations)
        for path_key, base_path_item in base_paths.items():
            if not isinstance(base_path_item, dict):
                continue

            target_path_item = target_paths.get(path_key)
            if target_path_item is None:
                findings.append({
                    "severity": ChangeSeverity.BREAKING.value,
                    "category": BreakingCategory.REMOVED_ENDPOINT.value,
                    "target": path_key,
                    "description": f"Endpoint path '{path_key}' was completely removed in {target_version}.",
                    "evidence": f"Base defined {list(base_path_item.keys())} at '{path_key}', but path is missing in target.",
                    "safe_migration_advice": "Mark endpoint as deprecated in OpenAPI spec using 'deprecated: true' before decommissioning in a future major version.",
                    "provenance": "CONFIRMED",
                })
                continue

            for method, base_op in base_path_item.items():
                if method.lower() not in valid_methods or not isinstance(base_op, dict):
                    continue

                method_upper = method.upper()
                endpoint_ref = f"{method_upper} {path_key}"

                target_op = target_path_item.get(method)
                if target_op is None or not isinstance(target_op, dict):
                    findings.append({
                        "severity": ChangeSeverity.BREAKING.value,
                        "category": BreakingCategory.CHANGED_METHOD.value,
                        "target": endpoint_ref,
                        "description": f"HTTP method {method_upper} for '{path_key}' was removed in {target_version}.",
                        "evidence": f"Method {method_upper} present in base specification, absent in target.",
                        "safe_migration_advice": f"Retain {method_upper} handler with HTTP 301/308 redirect or deprecation notice headers.",
                        "provenance": "CONFIRMED",
                    })
                    continue

                # Compare parameters
                base_params = {p.get("name"): p for p in base_op.get("parameters", []) if isinstance(p, dict) and "name" in p}
                target_params = {p.get("name"): p for p in target_op.get("parameters", []) if isinstance(p, dict) and "name" in p}

                for param_name, target_p in target_params.items():
                    base_p = base_params.get(param_name)
                    is_required_target = target_p.get("required", False)
                    is_required_base = base_p.get("required", False) if base_p else False

                    if is_required_target and not is_required_base:
                        findings.append({
                            "severity": ChangeSeverity.BREAKING.value,
                            "category": BreakingCategory.REQUIRED_PARAMETER_ADDED.value,
                            "target": f"{endpoint_ref} -> param:{param_name}",
                            "description": f"Parameter '{param_name}' is now strictly required in {target_version}.",
                            "evidence": f"Base required={is_required_base}, Target required=True",
                            "safe_migration_advice": "Provide a default fallback value or maintain optionality during transitional release.",
                            "provenance": "CONFIRMED",
                        })

                    # Check parameter type change
                    base_type = base_p.get("schema", {}).get("type") if base_p else None
                    target_type = target_p.get("schema", {}).get("type")
                    if base_type and target_type and base_type != target_type:
                        findings.append({
                            "severity": ChangeSeverity.BREAKING.value,
                            "category": BreakingCategory.INCOMPATIBLE_TYPE.value,
                            "target": f"{endpoint_ref} -> param:{param_name}",
                            "description": f"Parameter '{param_name}' type changed from '{base_type}' to '{target_type}'.",
                            "evidence": f"Base schema type={base_type}, Target schema type={target_type}",
                            "safe_migration_advice": "Support both representations using oneOf/anyOf in the OpenAPI schema during the transition window.",
                            "provenance": "CONFIRMED",
                        })

                # Compare Request Body
                base_req_body = base_op.get("requestBody", {})
                target_req_body = target_op.get("requestBody", {})
                if target_req_body.get("required", False) and not base_req_body.get("required", False):
                    findings.append({
                        "severity": ChangeSeverity.BREAKING.value,
                        "category": BreakingCategory.REQUIRED_PARAMETER_ADDED.value,
                        "target": f"{endpoint_ref} -> requestBody",
                        "description": f"Request body on '{endpoint_ref}' is now required in {target_version}.",
                        "evidence": "Base required=False/None, Target required=True",
                        "safe_migration_advice": "Allow requests without body with graceful server defaults.",
                        "provenance": "CONFIRMED",
                    })

                # Check Request Body Schema fields
                base_props = ChangeAnalyzerService._extract_schema_properties(base_req_body)
                target_props = ChangeAnalyzerService._extract_schema_properties(target_req_body)

                target_required_fields = ChangeAnalyzerService._extract_required_fields(target_req_body)
                base_required_fields = ChangeAnalyzerService._extract_required_fields(base_req_body)

                for req_field in target_required_fields:
                    if req_field not in base_required_fields:
                        findings.append({
                            "severity": ChangeSeverity.BREAKING.value,
                            "category": BreakingCategory.REQUIRED_PARAMETER_ADDED.value,
                            "target": f"{endpoint_ref} -> body.{req_field}",
                            "description": f"Request field '{req_field}' is now mandatory in {target_version}.",
                            "evidence": f"Newly added to required array: '{req_field}'",
                            "safe_migration_advice": "Do not make new body fields mandatory on existing API endpoints. Version the endpoint if required.",
                            "provenance": "CONFIRMED",
                        })

                # Compare Response Schema (200/201)
                base_responses = base_op.get("responses", {})
                target_responses = target_op.get("responses", {})

                for status_code in ["200", "201", 200, 201]:
                    str_code = str(status_code)
                    if str_code in base_responses and str_code in target_responses:
                        base_resp_props = ChangeAnalyzerService._extract_schema_properties(base_responses[str_code])
                        target_resp_props = ChangeAnalyzerService._extract_schema_properties(target_responses[str_code])

                        for prop_name, prop_meta in base_resp_props.items():
                            if prop_name not in target_resp_props:
                                findings.append({
                                    "severity": ChangeSeverity.BREAKING.value,
                                    "category": BreakingCategory.REMOVED_RESPONSE_FIELD.value,
                                    "target": f"{endpoint_ref} -> response[{str_code}].{prop_name}",
                                    "description": f"Response field '{prop_name}' removed from {str_code} response in {target_version}.",
                                    "evidence": f"Field '{prop_name}' existed in base response schema, removed in target schema.",
                                    "safe_migration_advice": "Retain response fields with null/deprecated status to avoid breaking client deserializers.",
                                    "provenance": "CONFIRMED",
                                })
                            else:
                                b_type = prop_meta.get("type")
                                t_type = target_resp_props[prop_name].get("type")
                                if b_type and t_type and b_type != t_type:
                                    findings.append({
                                        "severity": ChangeSeverity.BREAKING.value,
                                        "category": BreakingCategory.INCOMPATIBLE_TYPE.value,
                                        "target": f"{endpoint_ref} -> response[{str_code}].{prop_name}",
                                        "description": f"Response field '{prop_name}' changed type from '{b_type}' to '{t_type}'.",
                                        "evidence": f"Base type={b_type}, Target type={t_type}",
                                        "safe_migration_advice": "Do not change response types on existing endpoints. Add a new field or release a new API route.",
                                        "provenance": "CONFIRMED",
                                    })

        # 2. Check for Non-Breaking additions in Target
        for path_key, target_path_item in target_paths.items():
            if not isinstance(target_path_item, dict):
                continue
            base_path_item = base_paths.get(path_key)

            for method, target_op in target_path_item.items():
                if method.lower() not in valid_methods or not isinstance(target_op, dict):
                    continue
                method_upper = method.upper()
                endpoint_ref = f"{method_upper} {path_key}"

                if base_path_item is None or method not in base_path_item:
                    findings.append({
                        "severity": ChangeSeverity.NON_BREAKING.value,
                        "category": BreakingCategory.SCHEMA_RESTRICTION.value,
                        "target": endpoint_ref,
                        "description": f"New endpoint '{endpoint_ref}' introduced in {target_version}.",
                        "evidence": f"Target path {endpoint_ref} is backwards compatible.",
                        "safe_migration_advice": "Standard additive change. Safe to roll out.",
                        "provenance": "CONFIRMED",
                    })

        breaking_count = sum(1 for f in findings if f["severity"] == ChangeSeverity.BREAKING.value)
        non_breaking_count = sum(1 for f in findings if f["severity"] == ChangeSeverity.NON_BREAKING.value)

        analysis = ChangeAnalysis(
            organization_id=organization_id,
            project_id=project_id,
            author_id=author_id,
            title=title,
            analysis_type="openapi",
            base_version=base_version,
            target_version=target_version,
            breaking_count=breaking_count,
            non_breaking_count=non_breaking_count,
            findings=findings,
            metadata_info={
                "base_endpoints_count": len(base_paths),
                "target_endpoints_count": len(target_paths),
            },
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def compare_sql_migration(
        db: Session,
        organization_id: str,
        project_id: str,
        author_id: str,
        title: str,
        migration_filename: str,
        sql_content: str,
        base_version: str = "current_schema",
        target_version: str = "proposed_migration",
    ) -> ChangeAnalysis:
        if not sql_content or not sql_content.strip():
            raise HTTPException(status_code=400, detail="SQL migration script cannot be empty")
        if len(sql_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="SQL migration script exceeds 10MB size limit")

        findings: List[Dict[str, Any]] = []

        drop_table_pattern = re.compile(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([\"`\w\.]+)", re.IGNORECASE)
        drop_col_pattern = re.compile(r"ALTER\s+TABLE\s+([\"`\w\.]+)\s+DROP\s+COLUMN\s+([\"`\w]+)", re.IGNORECASE)
        alter_not_null_pattern = re.compile(r"ALTER\s+TABLE\s+([\"`\w\.]+)\s+ALTER\s+COLUMN\s+([\"`\w]+)\s+SET\s+NOT\s+NULL", re.IGNORECASE)
        alter_type_pattern = re.compile(r"ALTER\s+TABLE\s+([\"`\w\.]+)\s+ALTER\s+COLUMN\s+([\"`\w]+)\s+TYPE\s+([\"`\w]+)", re.IGNORECASE)
        create_table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\"`\w\.]+)", re.IGNORECASE)
        add_col_pattern = re.compile(r"ALTER\s+TABLE\s+([\"`\w\.]+)\s+ADD\s+COLUMN\s+([\"`\w]+)", re.IGNORECASE)

        # Destructive Table Drop
        for match in drop_table_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            findings.append({
                "severity": ChangeSeverity.BREAKING.value,
                "category": BreakingCategory.DROPPED_TABLE.value,
                "target": f"table:{table_name}",
                "description": f"Table '{table_name}' is dropped destructively in migration.",
                "evidence": match.group(0),
                "safe_migration_advice": "Verify that all services have ceased querying this table before dropping. Use a two-week deprecation window.",
                "provenance": "CONFIRMED",
            })

        # Destructive Column Drop
        for match in drop_col_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            col_name = match.group(2).replace('"', '').replace('`', '')
            findings.append({
                "severity": ChangeSeverity.BREAKING.value,
                "category": BreakingCategory.DROPPED_COLUMN.value,
                "target": f"table:{table_name} -> column:{col_name}",
                "description": f"Column '{col_name}' dropped from table '{table_name}'.",
                "evidence": match.group(0),
                "safe_migration_advice": "Follow expand-contract: stop writing/reading from column in application code first, then drop in subsequent release.",
                "provenance": "CONFIRMED",
            })

        # Breaking NOT NULL constraint addition
        for match in alter_not_null_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            col_name = match.group(2).replace('"', '').replace('`', '')
            findings.append({
                "severity": ChangeSeverity.BREAKING.value,
                "category": BreakingCategory.INCOMPATIBLE_COLUMN_MODIFICATION.value,
                "target": f"table:{table_name} -> column:{col_name}",
                "description": f"Column '{col_name}' in table '{table_name}' set to NOT NULL without backfill.",
                "evidence": match.group(0),
                "safe_migration_advice": "Backfill existing NULL values and set a server DEFAULT before applying NOT NULL constraint.",
                "provenance": "CONFIRMED",
            })

        # Column Type Alteration
        for match in alter_type_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            col_name = match.group(2).replace('"', '').replace('`', '')
            new_type = match.group(3).replace('"', '').replace('`', '')
            findings.append({
                "severity": ChangeSeverity.BREAKING.value,
                "category": BreakingCategory.INCOMPATIBLE_COLUMN_MODIFICATION.value,
                "target": f"table:{table_name} -> column:{col_name}",
                "description": f"Column '{col_name}' altered to type '{new_type}'.",
                "evidence": match.group(0),
                "safe_migration_advice": "Create a new column with the target type, dual-write, backfill, and switch reads before dropping old column.",
                "provenance": "CONFIRMED",
            })

        # Non-Breaking Additions
        for match in create_table_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            findings.append({
                "severity": ChangeSeverity.NON_BREAKING.value,
                "category": BreakingCategory.SCHEMA_RESTRICTION.value,
                "target": f"table:{table_name}",
                "description": f"New table '{table_name}' created.",
                "evidence": match.group(0),
                "safe_migration_advice": "Additive schema change. Safe to apply.",
                "provenance": "CONFIRMED",
            })

        for match in add_col_pattern.finditer(sql_content):
            table_name = match.group(1).replace('"', '').replace('`', '').split('.')[-1]
            col_name = match.group(2).replace('"', '').replace('`', '')
            findings.append({
                "severity": ChangeSeverity.NON_BREAKING.value,
                "category": BreakingCategory.SCHEMA_RESTRICTION.value,
                "target": f"table:{table_name} -> column:{col_name}",
                "description": f"New column '{col_name}' added to table '{table_name}'.",
                "evidence": match.group(0),
                "safe_migration_advice": "Ensure column is nullable or has an explicit default value.",
                "provenance": "CONFIRMED",
            })

        breaking_count = sum(1 for f in findings if f["severity"] == ChangeSeverity.BREAKING.value)
        non_breaking_count = sum(1 for f in findings if f["severity"] == ChangeSeverity.NON_BREAKING.value)

        analysis = ChangeAnalysis(
            organization_id=organization_id,
            project_id=project_id,
            author_id=author_id,
            title=title,
            analysis_type="sql_migration",
            base_version=base_version,
            target_version=target_version,
            breaking_count=breaking_count,
            non_breaking_count=non_breaking_count,
            findings=findings,
            metadata_info={
                "migration_filename": migration_filename,
                "sql_length_bytes": len(sql_content),
            },
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def _extract_schema_properties(content_dict: dict) -> Dict[str, Any]:
        """Helper to extract properties dict from OpenAPI requestBody or response content."""
        if not isinstance(content_dict, dict):
            return {}
        content = content_dict.get("content", {})
        # Check json content type
        for mime in ["application/json", "application/*+json"]:
            if mime in content and isinstance(content[mime], dict):
                schema = content[mime].get("schema", {})
                if "properties" in schema and isinstance(schema["properties"], dict):
                    return schema["properties"]
        # Direct schema
        schema = content_dict.get("schema", {})
        if "properties" in schema and isinstance(schema["properties"], dict):
            return schema["properties"]
        return {}

    @staticmethod
    def _extract_required_fields(content_dict: dict) -> List[str]:
        """Helper to extract required fields list from requestBody content."""
        if not isinstance(content_dict, dict):
            return []
        content = content_dict.get("content", {})
        for mime in ["application/json", "application/*+json"]:
            if mime in content and isinstance(content[mime], dict):
                schema = content[mime].get("schema", {})
                req = schema.get("required", [])
                if isinstance(req, list):
                    return req
        schema = content_dict.get("schema", {})
        req = schema.get("required", [])
        return req if isinstance(req, list) else []

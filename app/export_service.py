import io
import json
import os
import zipfile
from typing import Any

from app.database.models import Workflow
from app.quality_gate import deserialize_quality_gate


class ExportService:
    @staticmethod
    def export_json(workflow: Workflow) -> dict[str, Any]:
        """
        Build JSON export without mutating ORM objects.
        """
        wf_dict = workflow.to_dict()

        iterations = [
            it.to_dict()
            for it in sorted(workflow.iterations, key=lambda x: x.iteration_number)
        ]
        messages = [
            msg.to_dict()
            for msg in sorted(workflow.messages, key=lambda x: x.sequence_number)
        ]
        generated_files = [
            gf.to_dict()
            for gf in sorted(
                workflow.generated_files,
                key=lambda x: (not x.is_final, x.created_at or ""),
            )
        ]

        return {
            "workflow": wf_dict,
            "iterations": iterations,
            "messages": messages,
            "generated_files": generated_files,
        }

    @staticmethod
    def sanitize_path(filename: str) -> str:
        parts = [
            p for p in filename.strip().replace("\\", "/").split("/")
            if p and p != ".." and p != "."
        ]
        return "/".join(parts) if parts else "file.txt"

    @classmethod
    def export_zip(cls, workflow: Workflow) -> bytes:
        """
        Generate a ZIP archive containing structured iteration folders, final folder,
        root README.md, and quality-report.json.
        """
        buf = io.BytesIO()
        used_names: set[str] = set()

        qg_result = deserialize_quality_gate(workflow.quality_gate_data)
        is_passed = (workflow.status == "COMPLETE") and (qg_result.overall_status.value == "PASS")

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Write quality-report.json
            report_data = {
                "workflow_id": workflow.id,
                "prompt": workflow.prompt,
                "workflow_status": workflow.status,
                "quality_gate_status": qg_result.overall_status.value,
                "run_readiness": qg_result.run_readiness.value,
                "unresolved_imports": qg_result.project_validation.unresolved_imports,
                "undefined_symbols": qg_result.project_validation.undefined_symbols,
                "syntax_errors": qg_result.project_validation.syntax_errors,
                "module_conflicts": qg_result.project_validation.module_conflicts,
                "placeholder_files": qg_result.project_validation.placeholder_files,
                "missing_dependency_files": qg_result.project_validation.missing_dependency_files,
                "security_issues": qg_result.security_issues,
                "recommended_fixes": qg_result.recommended_fixes,
            }
            zf.writestr("quality-report.json", json.dumps(report_data, indent=2))
            used_names.add("quality-report.json")

            # 2. Write Root README.md
            readme_content = f"# Workflow: {workflow.prompt}\n\n"
            readme_content += f"**ID:** `{workflow.id}`  \n"
            readme_content += f"**Status:** {workflow.status}  \n"
            readme_content += f"**Quality Gate Status:** {qg_result.overall_status.value}  \n"
            readme_content += f"**Run Readiness:** {qg_result.run_readiness.value}  \n"
            readme_content += f"**Total Iterations:** {workflow.total_iterations}  \n"
            if workflow.final_summary:
                readme_content += f"\n## Summary\n\n{workflow.final_summary}\n"

            zf.writestr("README.md", readme_content)
            used_names.add("readme.md")

            # 3. Organize generated files into iterations/ and final/
            all_files = sorted(
                workflow.generated_files,
                key=lambda x: (not x.is_final, x.created_at or ""),
            )

            final_files = []

            for gf in all_files:
                raw_path = cls.sanitize_path(gf.filename or "file.txt")
                iter_num = 1
                if hasattr(gf, "iteration") and gf.iteration:
                    iter_num = gf.iteration.iteration_number

                # Place in iterations/iteration-N/
                iter_path = f"iterations/iteration-{iter_num}/{raw_path}"
                counter = 1
                base, ext = os.path.splitext(iter_path)
                final_iter_path = iter_path
                while final_iter_path.lower() in used_names:
                    final_iter_path = f"{base}_{counter}{ext}"
                    counter += 1
                used_names.add(final_iter_path.lower())
                zf.writestr(final_iter_path, gf.content or "")

                if gf.is_final:
                    final_files.append((raw_path, gf.content or ""))

            # 4. Handle final/ folder
            if is_passed and final_files:
                for raw_path, content in final_files:
                    fpath = f"final/{raw_path}"
                    counter = 1
                    base, ext = os.path.splitext(fpath)
                    final_fpath = fpath
                    while final_fpath.lower() in used_names:
                        final_fpath = f"{base}_{counter}{ext}"
                        counter += 1
                    used_names.add(final_fpath.lower())
                    zf.writestr(final_fpath, content)
            else:
                # Gate failed or no final files -> write final/README.md explaining no accepted final build
                no_final_readme = (
                    f"# No Accepted Final Build\n\n"
                    f"Workflow `{workflow.id}` did not pass Quality Gate checks.  \n"
                    f"Status: `{workflow.status}`  \n"
                    f"Quality Gate Status: `{qg_result.overall_status.value}`  \n"
                    f"Run Readiness: `{qg_result.run_readiness.value}`  \n\n"
                    f"Please review `quality-report.json` and iteration artifacts under `iterations/` for details.\n"
                )
                zf.writestr("final/README.md", no_final_readme)
                used_names.add("final/readme.md")

        buf.seek(0)
        return buf.getvalue()

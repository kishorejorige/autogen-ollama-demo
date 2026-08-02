import io
import os
import zipfile
from typing import Any

from app.database.models import Workflow


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
    def export_zip(workflow: Workflow) -> bytes:
        """
        Generate a ZIP archive containing generated source files and README (if available).
        Sanitizes all ZIP entry names to prevent path traversal and duplicate archive entry names.
        """
        buf = io.BytesIO()
        used_names: set[str] = set()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            has_readme = False

            files = sorted(
                workflow.generated_files,
                key=lambda x: (not x.is_final, x.created_at or ""),
            )

            for gf in files:
                raw_filename = (gf.filename or "file.txt").strip()

                # Sanitize filename to prevent path traversal
                cleaned_parts = [
                    part
                    for part in raw_filename.replace("\\", "/").split("/")
                    if part and part != ".." and part != "."
                ]
                sanitized_name = "/".join(cleaned_parts) if cleaned_parts else "file.txt"
                filename_only = os.path.basename(sanitized_name).lower()
                if filename_only in ("readme.md", "readme", "readme.txt"):
                    has_readme = True

                archive_name = sanitized_name
                counter = 1
                base, ext = os.path.splitext(sanitized_name)
                while archive_name.lower() in used_names:
                    archive_name = f"{base}_{counter}{ext}"
                    counter += 1

                used_names.add(archive_name.lower())
                zf.writestr(archive_name, gf.content or "")

            # Add README.md only when one does not already exist
            if not has_readme:
                readme_content = f"# Workflow: {workflow.prompt}\n\n"
                readme_content += f"**ID:** `{workflow.id}`  \n"
                readme_content += f"**Status:** {workflow.status}  \n"
                readme_content += f"**Total Iterations:** {workflow.total_iterations}  \n"
                if workflow.created_at:
                    readme_content += f"**Created At:** {workflow.created_at.isoformat()}  \n"
                if workflow.completed_at:
                    readme_content += f"**Completed At:** {workflow.completed_at.isoformat()}  \n"
                if workflow.final_summary:
                    readme_content += f"\n## Summary\n\n{workflow.final_summary}\n"

                readme_name = "README.md"
                counter = 1
                while readme_name.lower() in used_names:
                    readme_name = f"README_{counter}.md"
                    counter += 1
                used_names.add(readme_name.lower())

                zf.writestr(readme_name, readme_content)

        buf.seek(0)
        return buf.getvalue()

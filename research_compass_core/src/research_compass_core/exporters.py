"""Export functionality for research reports in multiple formats."""

import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for report exporters."""

    @abstractmethod
    async def export(self, markdown_content: str, output_path: str) -> str:
        """Export markdown content to target format.

        Args:
            markdown_content: The markdown content to export
            output_path: Full path where the file should be saved

        Returns:
            The path to the exported file
        """
        pass


class MarkdownExporter(BaseExporter):
    """Export report as Markdown file."""

    async def export(self, content: str, output_path: str) -> str:
        """Save markdown content to file."""
        Path(output_path).write_text(content, encoding='utf-8')
        return output_path


class HTMLExporter(BaseExporter):
    """Export report as HTML file with styling."""

    async def export(self, content: str, output_path: str) -> str:
        """Convert markdown to styled HTML."""
        try:
            import markdown

            # Convert markdown to HTML
            html_body = markdown.markdown(
                content,
                extensions=['extra', 'codehilite', 'tables', 'toc']
            )

            # Wrap in a styled HTML template
            html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; margin-top: 25px; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #555;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
    </style>
</head>
<body>
{html_body}
<hr>
<p style="color: #999; font-size: 0.9em; text-align: center;">
    Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
</p>
</body>
</html>"""

            Path(output_path).write_text(html_template, encoding='utf-8')
            return output_path

        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            raise


class PDFExporter(BaseExporter):
    """Export report as PDF file."""

    async def export(self, content: str, output_path: str) -> str:
        """Convert markdown to PDF via HTML intermediate."""
        try:
            import markdown
            from weasyprint import HTML

            # First convert markdown to HTML
            html_body = markdown.markdown(
                content,
                extensions=['extra', 'codehilite', 'tables', 'toc']
            )

            # Create PDF-optimized HTML
            html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Research Report</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
        }}
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            color: #000;
        }}
        h1 {{
            color: #000;
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
            page-break-after: avoid;
        }}
        h2 {{
            color: #000;
            border-bottom: 1px solid #666;
            padding-bottom: 5px;
            margin-top: 25px;
            page-break-after: avoid;
        }}
        h3 {{
            color: #333;
            margin-top: 20px;
            page-break-after: avoid;
        }}
        p {{ margin: 10px 0; }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        code {{
            background-color: #f0f0f0;
            padding: 2px 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-left: 3px solid #ccc;
            overflow-x: auto;
            page-break-inside: avoid;
        }}
        blockquote {{
            border-left: 3px solid #ccc;
            margin: 15px 0;
            padding-left: 15px;
            color: #555;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        th, td {{
            border: 1px solid #000;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #e0e0e0;
            font-weight: bold;
        }}
        .footer {{
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 0.8em;
            color: #666;
        }}
    </style>
</head>
<body>
{html_body}
<div class="footer">
    Generated on {datetime.now().strftime("%B %d, %Y")}
</div>
</body>
</html>"""

            # Convert HTML to PDF
            HTML(string=html_template).write_pdf(output_path)
            return output_path

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            raise


class DOCXExporter(BaseExporter):
    """Export report as Microsoft Word document."""

    async def export(self, content: str, output_path: str) -> str:
        """Convert markdown to DOCX format."""
        try:
            from docx import Document
            from docx.shared import Pt, RGBColor, Inches
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

            doc = Document()

            # Parse markdown line by line
            lines = content.split('\n')
            i = 0

            while i < len(lines):
                line = lines[i].rstrip()

                # Skip empty lines
                if not line:
                    i += 1
                    continue

                # Headers
                if line.startswith('# '):
                    heading = doc.add_heading(line[2:], level=1)
                    heading.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                elif line.startswith('## '):
                    heading = doc.add_heading(line[3:], level=2)
                    heading.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                elif line.startswith('### '):
                    heading = doc.add_heading(line[4:], level=3)
                    heading.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                elif line.startswith('#### '):
                    heading = doc.add_heading(line[5:], level=4)
                    heading.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

                # Bullet points
                elif line.startswith('- ') or line.startswith('* '):
                    doc.add_paragraph(line[2:], style='List Bullet')

                # Numbered lists
                elif re.match(r'^\d+\.\s', line):
                    text = re.sub(r'^\d+\.\s', '', line)
                    doc.add_paragraph(text, style='List Number')

                # Code blocks
                elif line.startswith('```'):
                    code_lines = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith('```'):
                        code_lines.append(lines[i])
                        i += 1
                    if code_lines:
                        code_para = doc.add_paragraph('\n'.join(code_lines))
                        code_para.style = 'Normal'
                        for run in code_para.runs:
                            run.font.name = 'Courier New'
                            run.font.size = Pt(9)
                            run.font.color.rgb = RGBColor(0, 0, 0)

                # Blockquotes
                elif line.startswith('> '):
                    quote_para = doc.add_paragraph(line[2:])
                    quote_para.paragraph_format.left_indent = Inches(0.5)
                    for run in quote_para.runs:
                        run.font.italic = True

                # Regular paragraphs
                else:
                    # Handle inline markdown in regular text
                    para = doc.add_paragraph()
                    self._add_formatted_text(para, line)

                i += 1

            # Add footer with generation date
            section = doc.sections[0]
            footer = section.footer
            footer_para = footer.paragraphs[0]
            footer_para.text = f"Generated on {datetime.now().strftime('%B %d, %Y')}"
            footer_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            doc.save(output_path)
            return output_path

        except Exception as e:
            logger.error(f"DOCX export failed: {e}")
            raise

    def _add_formatted_text(self, paragraph, text):
        """Add text to paragraph with inline formatting (bold, italic, links)."""
        from docx.shared import RGBColor

        # Simple regex patterns for markdown formatting
        # This is a basic implementation - could be enhanced

        # Handle links [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        parts = re.split(link_pattern, text)

        i = 0
        while i < len(parts):
            if i + 2 < len(parts) and parts[i + 1] and parts[i + 2]:
                # This is a link
                if parts[i]:
                    paragraph.add_run(parts[i])
                link_run = paragraph.add_run(parts[i + 1])
                link_run.font.color.rgb = RGBColor(0, 0, 255)
                link_run.font.underline = True
                i += 3
            else:
                if parts[i]:
                    # Handle bold **text**
                    bold_parts = re.split(r'\*\*([^\*]+)\*\*', parts[i])
                    for j, part in enumerate(bold_parts):
                        if j % 2 == 1:
                            paragraph.add_run(part).bold = True
                        else:
                            paragraph.add_run(part)
                i += 1


class JSONExporter(BaseExporter):
    """Export report as structured JSON."""

    async def export(self, content: str, output_path: str) -> str:
        """Convert markdown to structured JSON format."""
        try:
            # Parse markdown structure
            sections = []
            current_section = None
            sources = []

            lines = content.split('\n')
            in_sources = False

            for line in lines:
                line = line.rstrip()

                # Detect sources section
                if line.startswith('### Sources') or line.startswith('## Sources'):
                    in_sources = True
                    continue

                # Parse sources
                if in_sources and line.strip():
                    # Match [1] Source: URL pattern
                    source_match = re.match(r'\[(\d+)\]\s*(.+?):\s*(.+)', line)
                    if source_match:
                        sources.append({
                            "citation": int(source_match.group(1)),
                            "title": source_match.group(2).strip(),
                            "url": source_match.group(3).strip()
                        })
                    continue

                # Parse sections
                if line.startswith('# '):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "level": 1,
                        "title": line[2:],
                        "content": []
                    }
                elif line.startswith('## '):
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "level": 2,
                        "title": line[3:],
                        "content": []
                    }
                elif line.startswith('### ') and not in_sources:
                    if current_section:
                        sections.append(current_section)
                    current_section = {
                        "level": 3,
                        "title": line[4:],
                        "content": []
                    }
                elif current_section and line.strip():
                    current_section["content"].append(line)

            # Add last section
            if current_section:
                sections.append(current_section)

            # Build JSON structure
            report_json = {
                "generated_at": datetime.now().isoformat(),
                "sections": sections,
                "sources": sources,
                "raw_markdown": content
            }

            Path(output_path).write_text(
                json.dumps(report_json, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            return output_path

        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise


class TextExporter(BaseExporter):
    """Export report as plain text (strip markdown formatting)."""

    async def export(self, content: str, output_path: str) -> str:
        """Convert markdown to plain text."""
        try:
            # Remove markdown formatting
            text = content

            # Remove headers markup but keep text
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

            # Remove bold/italic
            text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^\*]+)\*', r'\1', text)
            text = re.sub(r'__([^_]+)__', r'\1', text)
            text = re.sub(r'_([^_]+)_', r'\1', text)

            # Convert links [text](url) to "text (url)"
            text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\1 (\2)', text)

            # Remove code block markers
            text = re.sub(r'```[^\n]*\n', '', text)
            text = re.sub(r'```', '', text)

            # Remove inline code markers
            text = re.sub(r'`([^`]+)`', r'\1', text)

            Path(output_path).write_text(text, encoding='utf-8')
            return output_path

        except Exception as e:
            logger.error(f"Text export failed: {e}")
            raise


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """Convert text to safe filename.

    Args:
        text: The text to sanitize
        max_length: Maximum length of the filename

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Lowercase and replace spaces with underscores
    safe = text.lower()
    safe = re.sub(r'[^\w\s-]', '', safe)  # Remove special characters
    safe = re.sub(r'[-\s]+', '_', safe)    # Replace spaces/hyphens with underscores
    safe = safe[:max_length].strip('_')     # Limit length and strip trailing underscores

    return safe if safe else 'research_report'


def generate_filename(research_brief: str) -> str:
    """Generate filename from research brief and timestamp.

    Args:
        research_brief: The research brief or topic

    Returns:
        Filename in format: {topic}_{timestamp}
    """
    topic = sanitize_filename(research_brief)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{topic}_{timestamp}"


async def export_report(
    markdown_content: str,
    research_brief: str,
    export_formats: List[str],
    export_dir: str
) -> Dict[str, str]:
    """Export report to multiple formats.

    Args:
        markdown_content: The markdown content to export
        research_brief: Research brief used for filename generation
        export_formats: List of format extensions (e.g., ['pdf', 'docx'])
        export_dir: Directory where files should be saved

    Returns:
        Dictionary mapping format to filepath for successfully exported files
    """
    print(f"📝 export_report called:")
    print(f"   Markdown length: {len(markdown_content)} chars")
    print(f"   Research brief: {research_brief}")
    print(f"   Export formats: {export_formats}")
    print(f"   Export directory: {export_dir}")

    # Create export directory if it doesn't exist
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    print(f"✓ Export directory created/verified: {export_dir}")

    # Generate base filename
    base_filename = generate_filename(research_brief)
    print(f"✓ Base filename: {base_filename}")

    # Initialize exporters
    exporters = {
        'md': MarkdownExporter(),
        'pdf': PDFExporter(),
        'html': HTMLExporter(),
        'docx': DOCXExporter(),
        'json': JSONExporter(),
        'txt': TextExporter(),
    }

    exported_files = {}

    # Export to each requested format
    for fmt in export_formats:
        try:
            print(f"\n🔄 Processing format: {fmt}")
            exporter = exporters.get(fmt)
            if not exporter:
                logger.warning(f"Unknown export format: {fmt}")
                print(f"   ⚠️  Unknown format: {fmt}")
                continue

            output_path = str(Path(export_dir) / f"{base_filename}.{fmt}")
            print(f"   Output path: {output_path}")

            filepath = await exporter.export(markdown_content, output_path)
            exported_files[fmt] = filepath
            logger.info(f"Successfully exported to {fmt}: {filepath}")
            print(f"   ✅ Successfully exported {fmt}: {filepath}")

        except Exception as e:
            # Log error but continue with other formats
            import traceback
            logger.error(f"Failed to export {fmt}: {e}")
            print(f"   ❌ Failed to export {fmt}: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

    print(f"\n📦 Export summary:")
    print(f"   Total formats requested: {len(export_formats)}")
    print(f"   Successfully exported: {len(exported_files)}")
    print(f"   Exported files: {exported_files}")

    return exported_files

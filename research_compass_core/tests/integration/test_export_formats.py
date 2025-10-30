#!/usr/bin/env python3
"""Test export functionality for research reports."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from research_compass_core import graph, ExportFormat
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Verify API key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Please set OPENAI_API_KEY in .env file")

async def test_export_formats():
    """Test exporting research report to multiple formats."""
    print("🧪 Testing Multi-Format Export Functionality")
    print("=" * 80)

    # Configure research with export formats
    config = {
        "configurable": {
            "thread_id": "test-export-session",
            "search_api": "arxiv",
            "research_model": "openai:gpt-4o-mini",
            "max_researcher_iterations": 1,  # Limit for quick test
            "allow_clarification": False,

            # Export configuration
            "export_formats": [
                ExportFormat.MARKDOWN,
                ExportFormat.PDF,
                ExportFormat.HTML,
                ExportFormat.DOCX,
                ExportFormat.JSON,
                ExportFormat.TXT,
            ],
            "export_directory": "./test_reports"
        }
    }

    # Simple research question
    question = "What is machine learning?"

    print(f"📝 Question: {question}")
    print(f"🔍 Search API: arxiv")
    print(f"🤖 Model: gpt-4o-mini")
    print(f"📄 Export Formats: MD, PDF, HTML, DOCX, JSON, TXT")
    print(f"📁 Export Directory: ./test_reports")
    print("=" * 80)
    print("\n🚀 Starting research and export...\n")

    try:
        # Run research with export
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=question)]},
            config=config
        )

        # Display results
        print("\n" + "=" * 80)
        print("📊 RESEARCH COMPLETE")
        print("=" * 80)

        # Show final report (truncated)
        report = result.get("final_report", "")
        if report:
            print("\n📄 Report Preview (first 500 chars):")
            print("-" * 80)
            print(report[:500] + "..." if len(report) > 500 else report)
            print("-" * 80)

        # Show exported files
        exported_files = result.get("exported_files", {})
        if exported_files:
            print(f"\n✅ Successfully exported to {len(exported_files)} formats:")
            print("-" * 80)
            for fmt, filepath in exported_files.items():
                file_exists = Path(filepath).exists()
                file_size = Path(filepath).stat().st_size if file_exists else 0
                status = "✓" if file_exists else "✗"
                print(f"  {status} {fmt.upper():6} → {filepath} ({file_size:,} bytes)")
            print("-" * 80)
        else:
            print("\n⚠️  No files were exported")

        print(f"\n✅ Test complete!")

        # Cleanup test files
        print("\n🧹 Cleaning up test files...")
        for filepath in exported_files.values():
            if Path(filepath).exists():
                Path(filepath).unlink()
                print(f"  Deleted: {filepath}")

        # Remove test directory if empty
        test_dir = Path("./test_reports")
        if test_dir.exists() and not list(test_dir.iterdir()):
            test_dir.rmdir()
            print(f"  Removed directory: {test_dir}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_no_export():
    """Test that not specifying export_formats doesn't create files."""
    print("\n" + "=" * 80)
    print("🧪 Testing No-Export Mode (Default Behavior)")
    print("=" * 80)

    config = {
        "configurable": {
            "thread_id": "test-no-export",
            "search_api": "arxiv",
            "research_model": "openai:gpt-4o-mini",
            "max_researcher_iterations": 1,
            "allow_clarification": False,
            # No export_formats specified
        }
    }

    print("\n🚀 Running research without export configuration...\n")

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="What is AI?")]},
            config=config
        )

        exported_files = result.get("exported_files", {})

        if not exported_files:
            print("✅ Correct: No files exported (default behavior)")
        else:
            print(f"⚠️  Unexpected: {len(exported_files)} files were exported")

        if result.get("final_report"):
            print("✅ Correct: Report still available in memory")
        else:
            print("❌ Error: Report not generated")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run both tests
    asyncio.run(test_export_formats())
    asyncio.run(test_no_export())

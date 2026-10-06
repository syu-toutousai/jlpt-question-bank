#!/usr/bin/env python3
"""
JLPT N1 Question Bank - Utility Script
Helps organize and manage questions in the question bank.
"""

import json
import os
from pathlib import Path
from datetime import datetime

class QuestionBank:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.past_exams = self.base_path / "past-exams"
        self.question_bank = self.base_path / "question-bank"
    
    def add_question(self, question_data: dict) -> str:
        """Add a new question to the question bank."""
        # Generate ID if not provided
        if "id" not in question_data:
            question_data["id"] = self._generate_id(question_data)
        
        # Add metadata
        question_data["created_at"] = datetime.now().isoformat()
        
        # Determine file path
        year = question_data.get("year", 0)
        month = question_data.get("month", 0)
        section = question_data.get("section", "unknown")
        q_type = question_data.get("type", "unknown")
        q_number = question_data.get("number", 0)
        
        # Save to past-exams/<year>/<month>/<section>
        past_exam_path = self.past_exams / str(year) / f"{month:02d}" / section
        past_exam_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{q_type}_{q_number:02d}.json"
        file_path = past_exam_path / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(question_data, f, ensure_ascii=False, indent=2)
        
        # Also save to question-bank/by-type
        by_type_path = self.question_bank / "by-type" / f"{section}-{q_type}"
        by_type_path.mkdir(parents=True, exist_ok=True)
        
        with open(by_type_path / filename, "w", encoding="utf-8") as f:
            json.dump(question_data, f, ensure_ascii=False, indent=2)
        
        return question_data["id"]
    
    def _generate_id(self, data: dict) -> str:
        """Generate a unique ID for a question."""
        year = data.get("year", 0)
        month = data.get("month", 0)
        section = data.get("section", "unknown")
        q_type = data.get("type", "unknown")
        q_number = data.get("number", 0)
        return f"{year}-{month:02d}-{section}-{q_type}-{q_number:02d}"
    
    def get_statistics(self) -> dict:
        """Get statistics about the question bank."""
        stats = {
            "total_questions": 0,
            "by_section": {},
            "by_type": {},
            "by_year": {}
        }
        
        for year_dir in self.past_exams.iterdir():
            if not year_dir.is_dir():
                continue
            year = year_dir.name
            stats["by_year"][year] = 0
            month_dirs = list(year_dir.iterdir())
            for month_dir in month_dirs:
                if month_dir.is_dir() and month_dir.name.isdigit():
                    for section_dir in month_dir.iterdir():
                        if section_dir.is_dir():
                            section = section_dir.name
                            stats["by_section"].setdefault(section, 0)
                            for q_file in section_dir.glob("*.json"):
                                stats["total_questions"] += 1
                                stats["by_section"][section] += 1
                                stats["by_year"][year] += 1
        
        return stats


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="JLPT N1 Question Bank Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new question")
    add_parser.add_argument("--year", type=int, required=True, help="Exam year")
    add_parser.add_argument("--month", type=int, required=True, help="Exam month (7 or 12)")
    add_parser.add_argument("--section", required=True, help="Section (vocab/grammar/reading/listening)")
    add_parser.add_argument("--type", required=True, help="Question type")
    add_parser.add_argument("--number", type=int, required=True, help="Question number")
    add_parser.add_argument("--question", required=True, help="Question text")
    add_parser.add_argument("--options", nargs=4, required=True, help="4 answer options")
    add_parser.add_argument("--answer", required=True, help="Correct answer")
    add_parser.add_argument("--explanation", help="Explanation")
    
    # Sync command: mirror past-exams into question-bank/by-type
    sync_parser = subparsers.add_parser("sync", help="Mirror past-exams/ into question-bank/by-type/")

    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    kb = QuestionBank()
    
    if args.command == "add":
        question_data = {
            "year": args.year,
            "month": args.month,
            "section": args.section,
            "type": args.type,
            "number": args.number,
            "question": args.question,
            "options": args.options,
            "answer": args.answer,
            "explanation": args.explanation or ""
        }
        q_id = kb.add_question(question_data)
        print(f"Added question: {q_id}")
    
    if args.command == "sync":
        from pathlib import Path as _P
        n = 0
        for qf in kb.past_exams.rglob("*.json"):
            d = json.load(open(qf, encoding="utf-8"))
            sect = d.get("section", "unknown")
            typ = d.get("type", "unknown")
            num = d.get("number", 0)
            out = kb.question_bank / "by-type" / f"{sect}-{typ}" / f"{typ}_{num:02d}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            n += 1
        print(f"Synced {n} questions into question-bank/by-type/")

    elif args.command == "stats":
        stats = kb.get_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

from pathlib import Path
import re
import argparse

CODE_PATTERNS = [
    r"\b(public|private|protected|static|final|class|interface|enum|void|int|long|double|float|boolean|String|new|return|if|else|for|while|switch|case|try|catch|throw)\b",
    r"[;{}]",
    r"\w+\s*\([^)]*\)\s*[;{]?",
    r"\w+\s*=\s*.+;",
    r"@\w+",
]

EXCLUDE_DIRS = {
    ".git", ".idea", ".vscode", "target", "build", "out",
    "node_modules", "dist", ".gradle", "__pycache__",
    ".gradle", ".mvn"
}

def looks_like_code(text: str) -> bool:
    line = text.strip()

    if not line:
        return False

    # обычные поясняющие комментарии
    normal_comment_words = [
        "todo", "fixme", "note", "описание", "пояснение",
        "пример", "важно", "author", "param", "return", "throws"
    ]

    lower = line.lower()
    if any(word in lower for word in normal_comment_words) and not any(x in line for x in [";", "{", "}", "="]):
        return False

    score = 0
    for pattern in CODE_PATTERNS:
        if re.search(pattern, line):
            score += 1

    # усиливаем уверенность, если строка прям похожа на Java-код
    if re.search(r"^\s*(public|private|protected|if|for|while|return|try|catch|class)\b", line):
        score += 2

    return score >= 2


def extract_comments_from_java(file_path: Path):
    results = []

    in_block = False
    block_start = None
    block_lines = []

    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for idx, original_line in enumerate(lines, start=1):
        line = original_line.rstrip("\n")

        if in_block:
            end_pos = line.find("*/")
            content = line[:end_pos] if end_pos != -1 else line
            content = content.strip().lstrip("*").strip()
            block_lines.append((idx, content))

            if end_pos != -1:
                suspicious = [
                    (num, txt) for num, txt in block_lines
                    if looks_like_code(txt)
                ]

                if suspicious:
                    results.append({
                        "type": "block",
                        "start": block_start,
                        "end": idx,
                        "lines": suspicious,
                        "snippet": "\n".join(text for _, text in suspicious)
                    })

                in_block = False
                block_start = None
                block_lines = []

            continue

        # ищем //
        line_comment_pos = line.find("//")
        block_comment_pos = line.find("/*")

        # если есть // раньше block-comment
        if line_comment_pos != -1 and (block_comment_pos == -1 or line_comment_pos < block_comment_pos):
            comment = line[line_comment_pos + 2:].strip()
            if looks_like_code(comment):
                results.append({
                    "type": "line",
                    "start": idx,
                    "end": idx,
                    "lines": [(idx, comment)]
                })

        # ищем /* ... */
        if block_comment_pos != -1:
            end_pos = line.find("*/", block_comment_pos + 2)

            # пропускаем Javadoc как документацию
            if line[block_comment_pos:block_comment_pos + 3] == "/**":
                continue

            if end_pos != -1:
                comment = line[block_comment_pos + 2:end_pos].strip()
                if looks_like_code(comment):
                    results.append({
                        "type": "block",
                        "start": idx,
                        "end": idx,
                        "lines": [(idx, comment)]
                    })
            else:
                in_block = True
                block_start = idx
                first_content = line[block_comment_pos + 2:].strip()
                block_lines = [(idx, first_content)]

    return results

def scan_project(project_path: Path):
    all_results = {}

    for file_path in project_path.rglob("*.java"):
        if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
            continue

        comments = extract_comments_from_java(file_path)
        if comments:
            all_results[file_path] = comments

    return all_results

def save_report(results, output_path="report.txt"):
    with open(output_path, "w", encoding="utf-8") as report:
        report.write("Java Dead Code Scanner Report\n")
        report.write("=============================\n\n")

        if not results:
            report.write("Подозрительно закомментированный код не найден.\n")
            return

        for file_path, comments in results.items():
            report.write(f"Файл: {file_path}\n")

            for item in comments:
                report.write(f"Строки {item['start']}-{item['end']} [{item['type']}]\n")

                for line_num, text in item["lines"]:
                    report.write(f"  {line_num}: {text}\n")

                report.write("\n")

def main():
    parser = argparse.ArgumentParser(description="Find commented-out dead Java code.")
    parser.add_argument("path", help="Path to Java project")
    args = parser.parse_args()

    project_path = Path(args.path)

    if not project_path.exists():
        print("Путь не найден.")
        return
    
    print("Java Dead Code Scanner")
    print("======================")

    results = scan_project(project_path)

    total_files = len(results)
    total_fragments = sum(len(comments) for comments in results.values())

    save_report(results)
    print("Report saved to report.txt")

    if not results:
        print("Подозрительно закомментированный код не найден.")
        return

    for file_path, comments in results.items():
        print(f"\nФайл: {file_path}")
        for item in comments:
            print("========================================")
            print("[DEAD CODE DETECTED]")
            print(f"File: {file_path}")
            print(f"Lines: {item['start']}-{item['end']}")
            print(f"Type: {item['type']}")
            print("Code:")
            if "snippet" in item:
                print(item["snippet"])
            else:
                for line_num, text in item["lines"]:
                    print(f"  {line_num}: {text}")
            print("========================================\n")

    print("Scan summary")
    print("============")
    print(f"Files with dead code: {total_files}")
    print(f"Dead code fragments: {total_fragments}")


if __name__ == "__main__":
    main()
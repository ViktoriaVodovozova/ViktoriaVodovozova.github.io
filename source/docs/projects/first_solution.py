import os
import re
import gc
import shutil
import zipfile
from pathlib import Path

import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict


def clean_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def extract_doc_id(pdf_path: Path) -> str:
    """
    document_053.pdf -> '53'
    """
    match = re.search(r"document_(\d+)", pdf_path.stem)
    if match:
        return str(int(match.group(1)))
    return pdf_path.stem


def remove_invalid_image_links(md_text: str, output_dir: Path) -> str:
    """
    Удаляет из markdown ссылки на картинки, которых реально нет.
    """
    pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    parts = []
    last_end = 0

    for match in pattern.finditer(md_text):
        parts.append(md_text[last_end:match.start()])

        alt_text = match.group(1)
        img_path = match.group(2).strip()

        full_img_path = output_dir / img_path
        if full_img_path.exists():
            parts.append(match.group(0))

        last_end = match.end()

    parts.append(md_text[last_end:])
    cleaned = "".join(parts)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip() + "\n"
    return cleaned


def make_submission_zip(output_dir: Path, zip_name: str = "submission.zip"):
    """
    Создаёт submission.zip со структурой:
    submission.zip
    ├── document_001.md
    ├── ...
    └── images/
        ├── doc_1_image_1.png
        └── ...
    """
    zip_path = Path(zip_name)
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for md_file in sorted(output_dir.glob("*.md")):
            zf.write(md_file, arcname=md_file.name)

        images_dir = output_dir / "images"
        if images_dir.exists():
            for img_file in sorted(images_dir.glob("*.png")):
                zf.write(img_file, arcname=f"images/{img_file.name}")

    print(f"Архив создан: {zip_path.resolve()}")


def run_conversion():
    input_dir = Path("pdfs")
    output_dir = Path("output")
    images_dir = output_dir / "images"

    # Полностью очищаем output перед запуском
    if output_dir.exists():
        shutil.rmtree(output_dir)

    images_dir.mkdir(parents=True, exist_ok=True)

    print("Инициализация моделей marker...")
    artifacts = create_model_dict()
    converter = PdfConverter(artifact_dict=artifacts)

    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        print("В папке pdfs нет PDF файлов.")
        return

    for pdf_path in pdf_files:
        print(f"--> Обработка: {pdf_path.name}")
        doc_id = extract_doc_id(pdf_path)

        try:
            result = converter(str(pdf_path))

            # В разных версиях marker markdown/images могут лежать немного по-разному
            md_text = getattr(result, "markdown", None)
            if md_text is None:
                md_text = getattr(result, "text", "")

            images = getattr(result, "images", {}) or {}

            image_idx = 1
            for internal_name, img_obj in images.items():
                new_img_name = f"doc_{doc_id}_image_{image_idx}.png"
                new_img_path = images_dir / new_img_name

                # Сохраняем картинку
                img_obj.save(new_img_path)

                # Меняем ссылку в markdown на правильную
                md_text = md_text.replace(
                    f"({internal_name})",
                    f"(images/{new_img_name})"
                )

                image_idx += 1

            # Удаляем битые ссылки на картинки
            md_text = remove_invalid_image_links(md_text, output_dir)

            # Сохраняем markdown
            md_output_path = output_dir / f"{pdf_path.stem}.md"
            with open(md_output_path, "w", encoding="utf-8") as f:
                f.write(md_text)

        except Exception as e:
            print(f"!!! Ошибка в файле {pdf_path.name}: {e}")

        clean_memory()

    make_submission_zip(output_dir)
    print("\nВсе готово. Результаты в папке output/")


if __name__ == "__main__":
    if not Path("pdfs").exists():
        print("Папка 'pdfs' не найдена!")
    else:
        run_conversion()
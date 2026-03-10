import argparse
from generator.pdf_utils import extract_pages
from generator.image_utils import save_image


def main():
    parser = argparse.ArgumentParser(
        description="Generate dataset from a PDF using LibrEd generator"
    )

    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to input PDF file"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Directory where generated images will be stored"
    )

    args = parser.parse_args()

    print(f"Processing PDF: {args.pdf}")

    pages = extract_pages(args.pdf)

    for i, page in enumerate(pages):
        save_image(page, args.output, i)

    print(f"Dataset successfully generated in {args.output}")


if __name__ == "__main__":
    main()

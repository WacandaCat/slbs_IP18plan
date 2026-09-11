
# ---------------------------------------------------------------- write
def main():
    out = {"generated_by": "data3.py", "langs": ["zh", "en", "ko"], "pages": PAGES}
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "dist", "data.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote", dst, os.path.getsize(dst), "bytes;", ", ".join(PAGES))

if __name__ == "__main__":
    main()

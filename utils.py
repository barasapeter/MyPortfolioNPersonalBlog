import re
import unicodedata


def generate_slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


if __name__ == "__main__":
    title = "My First Blog Post! hey"
    slug = generate_slug(title)
    print(slug)

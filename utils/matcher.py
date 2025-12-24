import unicodedata


def normalize(text):
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn").lower()


def smart_match(keyword, text):
    k, t = normalize(keyword), normalize(text)
    if t.startswith(k):
        return 3
    if any(w.startswith(k) for w in t.split()):
        return 2
    if k in t:
        return 1
    return 0

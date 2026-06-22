import sys
import os

# Heuristic: RU markers: ы ъ э ё, UK markers: і ї є ґ
# Shared but useful: и is shared, but in Russian it's the primary 'i' sound. 
# In Ukrainian 'і' is the primary 'i' sound and 'и' is 'y'.
# If 'и' is present but 'і' is absent, it's a strong hint for Russian.

def detect_lang_improved(text: str) -> str:
    lo = text.lower()
    
    # Check for English
    latin = sum(1 for c in lo if c.isalpha() and c.isascii())
    cyrillic = sum(1 for c in lo if '\u0400' <= c <= '\u04FF')
    if latin > cyrillic and latin > 0:
        return 'en'
    
    # Language-specific markers
    uk_markers = sum(1 for c in lo if c in 'їієґ')
    ru_markers = sum(1 for c in lo if c in 'ыъэё')
    
    if uk_markers > ru_markers:
        return 'uk'
    if ru_markers > uk_markers:
        return 'ru'
    
    # If ambiguous (both 0 or equal)
    # Check for 'и' (Russian 'i', Ukrainian 'y') vs 'і' (Ukrainian 'i')
    has_ru_marker = any(c in lo for c in 'и') # Russian 'и'
    has_uk_marker = any(c in lo for c in 'і') # Ukrainian 'і'
    
    if has_ru_marker and not has_uk_marker:
        return 'ru'
    if has_uk_marker and not has_ru_marker:
        return 'uk'
        
    # Final default
    return 'ru' # Default to Russian as per user's primary language usage

test_cases = [
    ("Привет мир", "ru"), # Common Russian
    ("Привіт світ", "uk"), # Common Ukrainian
    ("Мама мыла раму", "ru"), # Russian with 'ы'
    ("Ми йдемо", "uk"), # Ukrainian with 'и' (shared)
    ("Я здоровий і сильний", "uk"), # Ukrainian with 'і'
    ("Я здоровый и сильный", "ru"), # Russian with 'и'
    ("Hello world", "en"),
]

print(f"{'Text':<25} | {'Expected':<8} | {'Got':<8} | {'Status'}")
print("-" * 55)
for text, expected in test_cases:
    got = detect_lang_improved(text)
    status = "✅" if got == expected else "❌"
    print(f"{text:<25} | {expected:<8} | {got:<8} | {status}")

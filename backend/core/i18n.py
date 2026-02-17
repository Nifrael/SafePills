import json
import os
from typing import Dict, Any, Optional

class I18nService:
    _instances: Dict[str, Any] = {}
    _default_lang = "fr"
    _locales_dir = os.path.join(os.path.dirname(__file__), "../data/locales")

    def __init__(self):
        self._load_locales()

    def _load_locales(self):
        self._translations = {}
        for filename in os.listdir(self._locales_dir):
            if filename.endswith(".json"):
                lang = filename.split(".")[0]
                try:
                    with open(os.path.join(self._locales_dir, filename), "r", encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
                except Exception as e:
                    print(f"Error loading locale {lang}: {e}")

    def get(self, key: str, lang: str = "fr", section: str = "questions") -> Optional[str]:
        lang = lang if lang in self._translations else self._default_lang
        
        try:
            return self._translations.get(lang, {}).get(section, {}).get(key)
        except:
            return None

    def translate_question(self, question_id: str, default_text: str, lang: str) -> str:
        translated = self.get(question_id, lang, "questions")
        return translated if translated else default_text

    def translate_option(self, option_label_key: str, default_label: str, lang: str) -> str:
        translated = self.get(option_label_key, lang, "options")
        return translated if translated else default_label

    def get_advice(self, substance: str, key: str, lang: str = "fr") -> list:
        """
        Retrieves a list of advice strings for a given substance and key.
        """
        # Try target lang
        advice_section = self._translations.get(lang, {}).get("advice", {})
        substance_advice = advice_section.get(substance, {})
        tips = substance_advice.get(key)
        
        if tips:
            return tips
            
        # Fallback to default lang
        if lang != "fr":
            advice_section = self._translations.get("fr", {}).get("advice", {})
            substance_advice = advice_section.get(substance, {})
            tips = substance_advice.get(key)
            if tips:
                return tips
                
        return []

i18n = I18nService()

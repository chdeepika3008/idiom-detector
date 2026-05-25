from transformers import pipeline

# Use multilingual translation model
translator = pipeline("translation", model="facebook/nllb-200-distilled-600M")

def translate_to_telugu(text):
    result = translator(text, src_lang="eng_Latn", tgt_lang="tel_Telu")
    return result[0]["translation_text"]
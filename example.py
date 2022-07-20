from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TranslationPipeline

tokenizer = AutoTokenizer.from_pretrained("praeclarum/cuneiform")
model = AutoModelForSeq2SeqLM.from_pretrained("praeclarum/cuneiform", max_length=tokenizer.model_max_length)
pipeline = TranslationPipeline(model=model, tokenizer=tokenizer)

def translate(akkadian):
    return pipeline(f"translate Akkadian to English: {akkadian}")[0]["translation_text"]

print(translate("1(disz){d}szul3-ma-nu-_sag man gal?_-u2 _man_ dan-nu _man kisz_"))

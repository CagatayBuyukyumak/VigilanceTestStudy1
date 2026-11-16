"""Question texts of Study 1. Pure Python (no PsychoPy), shared by the task and the data scripts.

Each item: ("text", column, prompt) or ("likert", column, prompt, 1-anchor, 5-anchor).
"""

# The phrase participants type when a memory is too private to describe (instructions and question 1).
PRIVATE_PHRASE = "Belirtmek istemiyorum"

# Thought probe after every SPACE press (ethics form, Appendix F), in order.
PROBE = [
    ("text", "q1_description", "Lütfen aklınıza geleni birkaç kelimeyle yazınız. Çok özel bir anıysa "
     f"\"{PRIVATE_PHRASE}\" yazınız. (Boş bırakabilirsiniz.)"),
    ("likert", "q2_intentionality", "Bu aklınıza gelmeden hemen önce bilinçli olarak bir şeyi aklınıza "
     "getirmeye çalışıyor muydunuz?", "Kesinlikle hayır", "Kesinlikle evet"),
    ("likert", "q3_effort", "Bunun aklınıza gelmesi için ne kadar çaba harcadınız?",
     "Hiç çaba harcamadım", "Çok fazla çaba harcadım"),
    ("text", "q4_trigger", "Sizce bunu ne tetikledi?"),
    ("likert", "q5_relatedness", "Bu, sizce onu tetikleyen kelimeyle ne kadar güçlü bir şekilde bağlantılıydı?",
     "Hiç ilişkili değil", "Çok güçlü bir şekilde ilişkili"),
    ("likert", "q6_expectancy", "Aklınıza gelmeden hemen önce bir düşüncenin gelmesini bekliyor muydunuz?",
     "Hiç", "Tamamen"),
    ("likert", "q7_vividness", "Aklınıza geldiğinde ne kadar net ve canlıydı?", "Hiç net değil", "Son derece net"),
    ("likert", "q8_specificity", "Belirli bir zamanda ve yerde yaşanmış belirli bir kişisel olayla mı ilgiliydi?",
     "Kesinlikle hayır", "Kesinlikle evet"),
]

# Asked once, after the last slide. The study-purpose question comes first, before any question that
# mentions the words, so the later questions cannot suggest the answer.
POST = [
    ("text", "post_study_purpose", "Sizce bu çalışma ne ile ilgiliydi? Birkaç cümleyle yazınız."),
    ("likert", "post_boredom", "Çalışma ne kadar sıkıcıydı?", "Hiç sıkıcı değildi", "Çok sıkıcıydı"),
    ("text", "post_words_recall", "Görev sırasında ekranda gördüğünüz kelimelerden hatırladıklarınızı yazınız. "
     "(Hatırlamıyorsanız boş bırakabilirsiniz.)"),
    ("likert", "post_words_read", "Görev sırasında ekranda beliren kelimeleri ne sıklıkla okudunuz?",
     "Hiç okumadım", "Her zaman okudum"),
    ("likert", "post_words_attention", "Kelimeler dikkatinizi ne ölçüde çekti?", "Hiç çekmedi", "Çok fazla çekti"),
    ("likert", "post_words_triggered", "Sizce kelimeler aklınıza gelen düşünceleri ne ölçüde tetikledi?",
     "Hiç", "Çok fazla"),
    ("likert", "post_words_strategy", "Görev sırasında kelimeleri kullanarak bilinçli olarak bir şeyler "
     "hatırlamaya çalıştınız mı?", "Hiç", "Çok sık"),
]
POST_COLS = [item[1] for item in POST]
POST_TEXT_COLS = [item[1] for item in POST if item[0] == "text"]


def _tr_lower(text):
    return text.replace("İ", "i").replace("I", "ı").lower()


def is_private(answer):
    """1 if the description says the memory is private ("belirtmek istemiyorum", any capitalisation,
    with or without Turkish letters), else 0."""
    t = _tr_lower(str(answer or ""))
    t = t.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    return int("belirtmek istemiyorum" in " ".join(t.split()))

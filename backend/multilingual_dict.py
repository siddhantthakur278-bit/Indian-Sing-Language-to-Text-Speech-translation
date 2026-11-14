"""
Multilingual verified dictionary for 10 Indian scheduled languages.
Provides immediate offline translation fallback for standard ISL expressions
without requiring network access or external translation APIs.
"""

from typing import Dict, Optional

# Supported languages per Section 7.2
# en (English), hi (Hindi), mr (Marathi), ta (Tamil), bn (Bengali),
# te (Telugu), gu (Gujarati), kn (Kannada), ml (Malayalam), pa (Punjabi)

MULTILINGUAL_DICTIONARY: Dict[str, Dict[str, str]] = {
    # Emergency phrases
    "Please help me immediately!": {
        "en": "Please help me immediately!",
        "hi": "कृपया तुरंत मेरी मदद करें!",
        "mr": "कृपया मला लगेच मदत करा!",
        "ta": "தயவுசெய்து எனக்கு உடனே உதவுங்கள்!",
        "bn": "দয়া করে আমাকে অবিলম্বে সাহায্য করুন!",
        "te": "దయచేసి నాకు తక్షణమే సహాయం చేయండి!",
        "gu": "કૃપા કરીને તરત જ મારી મદદ કરો!",
        "kn": "ದಯವಿಟ್ಟು ತಕ್ಷಣ ನನಗೆ ಸಹಾಯ ಮಾಡಿ!",
        "ml": "ദയവായി എന്നെ ഉടൻ സഹായിക്കൂ!",
        "pa": "ਕਿਰਪਾ ਕਰਕੇ ਤੁਰੰਤ ਮੇਰੀ ਮਦਦ ਕਰੋ!",
    },
    "I need a doctor urgently.": {
        "en": "I need a doctor urgently.",
        "hi": "मुझे तत्काल डॉक्टर की आवश्यकता है।",
        "mr": "मला तातडीने डॉक्टरांची गरज आहे.",
        "ta": "எனக்கு உடனடியாக ஒரு மருத்துவர் தேவை.",
        "bn": "আমার অবিলম্বে একজন ডাক্তারের প্রয়োজন।",
        "te": "నాకు వెంటనే డాక్టర్ కావాలి.",
        "gu": "મને તાત્કાલિક ડૉક્ટરની જરૂર છે.",
        "kn": "ನನಗೆ ತಕ್ಷಣ ವೈದ್ಯರ ಅಗತ್ಯವಿದೆ.",
        "ml": "എനിക്ക് ഉടൻ ഒരു ഡോക്ടറെ ആവശ്യമുണ്ട്.",
        "pa": "ਮੈਨੂੰ ਤੁਰੰਤ ਡਾਕਟਰ ਦੀ ਲੋੜ ਹੈ।",
    },
    "Call an ambulance!": {
        "en": "Call an ambulance!",
        "hi": "कृपया तुरंत एम्बुलेंस को कॉल करें!",
        "mr": "रुग्णवाहिका बोलवा!",
        "ta": "ஆம்புலன்ஸை அழையுங்கள்!",
        "bn": "অ্যাম্বুলেন্স ডাকুন!",
        "te": "అంబులెన్స్ కు కాల్ చేయండి!",
        "gu": "એમ્બ્યુલન્સ બોલાવો!",
        "kn": "ಆಂಬ್ಯುಲೆನ್ಸ್ ಕರೆಯಿರಿ!",
        "ml": "ആംബുലൻസ് വിളിക്കൂ!",
        "pa": "ਐਂਬੂਲੈਂਸ ਬੁਲਾਓ!",
    },
    "Call the police now!": {
        "en": "Call the police now!",
        "hi": "कृपया तुरंत पुलिस को बुलाएं!",
        "mr": "ताबडतोब पोलिसांना बोलवा!",
        "ta": "உடனே போலீஸை அழையுங்கள்!",
        "bn": "এখনই পুলিশকে ডাকুন!",
        "te": "ఇప్పుడే పోలీసులను పిలవండి!",
        "gu": "હમણાં જ પોલીસને બોલાવો!",
        "kn": "ಈಗಲೇ ಪೊಲೀಸರನ್ನು ಕರೆಯಿರಿ!",
        "ml": "ഇപ്പോൾ തന്നെ പോലീസിനെ വിളിക്കൂ!",
        "pa": "ਹੁਣੇ ਪੁਲਿਸ ਨੂੰ ਬੁਲਾਓ!",
    },
    "I am in severe pain.": {
        "en": "I am in severe pain.",
        "hi": "मुझे बहुत तेज असहनीय दर्द हो रहा है।",
        "mr": "मला तीव्र वेदना होत आहेत.",
        "ta": "எனக்கு கடுமையான வலி உள்ளது.",
        "bn": "আমার তীব্র ব্যথা হচ্ছে।",
        "te": "నాకు తీవ్రమైన నొప్పిగా ఉంది.",
        "gu": "મને અતિશય દુખાવો થઈ રહ્યો છે.",
        "kn": "ನನಗೆ ತೀವ್ರ ನೋವಾಗುತ್ತಿದೆ.",
        "ml": "എനിക്ക് കഠിനമായ വേദനയുണ്ട്.",
        "pa": "ਮੈਨੂੰ ਬਹੁਤ ਤੇਜ਼ ਦਰਦ ਹੋ ਰਿਹਾ ਹੈ।",
    },
    # Common conversational phrases
    "I need to go to the hospital.": {
        "en": "I need to go to the hospital.",
        "hi": "मुझे अस्पताल जाना है।",
        "mr": "मला रुग्णालयात जायचे आहे.",
        "ta": "நான் மருத்துவமனைக்குச் செல்ல வேண்டும்.",
        "bn": "আমার হাসপাতালে যাওয়া দরকার।",
        "te": "నేను ఆసుపత్రికి వెళ్ళాలి.",
        "gu": "મારે હોસ્પિટલ જવું છે.",
        "kn": "ನಾನು ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಬೇಕು.",
        "ml": "എനിക്ക് ആശുപത്രിയിൽ പോകണം.",
        "pa": "ਮੈਨੂੰ ਹਸਪਤਾਲ ਜਾਣਾ ਪਵੇਗਾ।",
    },
    "I want water.": {
        "en": "I want water.",
        "hi": "मुझे पानी चाहिए।",
        "mr": "मला पाणी हवे आहे.",
        "ta": "எனக்கு தண்ணீர் வேண்டும்.",
        "bn": "আমার জল চাই।",
        "te": "నాకు నీరు కావాలి.",
        "gu": "મને પાણી જોઈએ છે.",
        "kn": "ನನಗೆ ನೀರು ಬೇಕು.",
        "ml": "എനിക്ക് വെള്ളം വേണം.",
        "pa": "ਮੈਨੂੰ ਪਾਣੀ ਚਾਹੀਦਾ ਹੈ।",
    },
    "Hello, friend.": {
        "en": "Hello, friend.",
        "hi": "नमस्ते दोस्त।",
        "mr": "नमस्कार मित्रा.",
        "ta": "வணக்கம் நண்பா.",
        "bn": "নমস্কার বন্ধু।",
        "te": "నమస్తే మిత్రమా.",
        "gu": "નમસ્તે મિત્ર.",
        "kn": "ನಮಸ್ಕಾರ ಸ್ನೇಹಿತರೇ.",
        "ml": "ഹലോ സുഹൃത്തേ.",
        "pa": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ ਦੋਸਤ।",
    },
    "Thank you very much.": {
        "en": "Thank you very much.",
        "hi": "आपका बहुत-बहुत धन्यवाद।",
        "mr": "खूप खूप धन्यवाद.",
        "ta": "மிக்க நன்றி.",
        "bn": "আপনাকে অনেক ধন্যবাদ।",
        "te": "చాలా ధన్యవాదాలు.",
        "gu": "ખૂબ ખૂબ આભાર.",
        "kn": "ತುಂಬಾ ಧನ್ಯವಾದಗಳು.",
        "ml": "വളരെ നന്ദി.",
        "pa": "ਤੁਹਾਡਾ ਬਹੁਤ ਬਹੁਤ ਧੰਨਵਾਦ।",
    },
    "What is your name?": {
        "en": "What is your name?",
        "hi": "आपका नाम क्या है?",
        "mr": "तुमचे नाव काय आहे?",
        "ta": "உங்கள் பெயர் என்ன?",
        "bn": "আপনার নাম কি?",
        "te": "మీ పేరు ఏమిటి?",
        "gu": "તમારું નામ શું છે?",
        "kn": "ನಿಮ್ಮ ಹೆಸರೇನು?",
        "ml": "നിങ്ങളുടെ പേരെന്താണ്?",
        "pa": "ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ?",
    },
}

def lookup_multilingual_phrase(english_text: str, target_lang: str) -> Optional[str]:
    """
    Search verified dictionary for offline translation.
    Returns translated string if found, otherwise None.
    """
    cleaned = english_text.strip()
    if cleaned in MULTILINGUAL_DICTIONARY:
        translations = MULTILINGUAL_DICTIONARY[cleaned]
        return translations.get(target_lang)
    return None

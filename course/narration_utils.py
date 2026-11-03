"""Dependency-light text and timing utilities shared by build and tests."""
import hashlib,json,re,unicodedata

def sentences(text):
    return re.split(r'(?<=[.!?])\s+',text.strip())

def chunks(text,limit=290):
    """Preserve complete sentences, unlike character-width TTS line splitting."""
    groups=[];current=''
    for sentence in sentences(text):
        if current and len(current)+len(sentence)+1>limit:
            groups.append(current);current=''
        current=(current+' '+sentence).strip()
    if current:groups.append(current)
    return groups

def speech_text(text,engine,lexicon):
    # Replace once, longest keys first, so phoneme annotations are never reprocessed.
    regex='|'.join(re.escape(k) for k in sorted(lexicon,key=len,reverse=True))
    return re.sub(regex,lambda m:lexicon[m.group()][engine],text)

def normalized_words(text):
    text=unicodedata.normalize('NFKD',text.lower()).encode('ascii','ignore').decode()
    text=re.sub(r'(?<=\d),(?=\d)','',text)
    def integer_words(n):
        small=['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen']
        tens=['','','twenty','thirty','forty','fifty','sixty','seventy','eighty','ninety']
        if n<20:return small[n]
        if n<100:return tens[n//10]+(' '+small[n%10] if n%10 else '')
        if n<1000:return small[n//100]+' hundred'+(' '+integer_words(n%100) if n%100 else '')
        if n<1000000:return integer_words(n//1000)+' thousand'+(' '+integer_words(n%1000) if n%1000 else '')
        return str(n)
    def number(m):
        whole,*fraction=m.group().split('.')
        return integer_words(int(whole))+(' point '+' '.join(integer_words(int(d)) for d in fraction[0]) if fraction else '')
    text=re.sub(r'\d+(?:\.\d+)?',number,text).replace('%',' percent ')
    for n in range(10,20):
        text=re.sub(r'\b'+integer_words(n)+r' hundred\b',integer_words(n*100),text)
    text=text.replace('dee rack','dirac').replace('dee-rack','dirac').replace('her mish un','hermitian').replace('her-mish-un','hermitian').replace('pow lee','pauli').replace('pow-lee','pauli').replace('paulie','pauli')
    text=text.replace('wavefunction','wave function').replace('planck','plank')
    text=text.replace('nonrectangular','non rectangular')
    text=text.replace('electronvolts','electron volts').replace('electronvolt','electron volt').replace('nanometres','nanometers')
    text=text.replace('shroh-ding-er','schrodinger').replace('shroh ding er','schrodinger')
    text=text.replace('schroedinger','schrodinger').replace('shrodinger','schrodinger')
    text=text.replace('one-dimensional','one dimensional').replace('time-independent','time independent')
    return re.findall(r"[a-z0-9]+",text)

def word_error_rate(expected,observed):
    a,b=normalized_words(expected),normalized_words(observed)
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        row=[i]
        for j,y in enumerate(b,1):row.append(min(row[-1]+1,prev[j]+1,prev[j-1]+(x!=y)))
        prev=row
    return prev[-1]/max(1,len(a))

def cache_key(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]

def frame_duration(seconds,fps=30):
    import math
    return math.ceil((seconds-1e-10)*fps)/fps

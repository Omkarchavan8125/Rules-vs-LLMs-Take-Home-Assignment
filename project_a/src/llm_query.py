import os,requests
def parse_with_gemini(text):
 key=os.getenv('GEMINI_API_KEY')
 if not key:return {'status':'disabled','message':'Set GEMINI_API_KEY for optional Gemini free-tier parser.'}
 url='https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key='+key
 r=requests.post(url,json={'contents':[{'parts':[{'text':'Extract facts and ambiguities only, do not calculate tax: '+text}]}]},timeout=20);r.raise_for_status();return r.json()

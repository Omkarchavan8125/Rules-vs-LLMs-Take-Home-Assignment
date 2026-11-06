import re
def parse(s):
 m=re.search(r'(?:salary|income|package|earn)[^0-9]{0,25}(?:₹|rs\\.?|inr)?\\s*([0-9][0-9,]*)',s.lower())
 if not m:return {'status':'clarification_required','question':'What is your annual gross salary in INR?'}
 v=int(m.group(1).replace(',',''))
 return {'status':'needs_confirmation','structured':{'salary':v},'question':'Confirm annual salary and provide deductions/HRA explicitly; no assumptions will be made.'}

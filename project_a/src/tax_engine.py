SLABS={'2024-25':{'old':[(250000,0),(500000,.05),(1000000,.20),(10**18,.30)],'new':[(300000,0),(700000,.05),(1000000,.10),(1200000,.15),(1500000,.20),(10**18,.30)]},'2025-26':{'old':[(250000,0),(500000,.05),(1000000,.20),(10**18,.30)],'new':[(400000,0),(800000,.05),(1200000,.10),(1600000,.15),(2000000,.20),(2400000,.25),(10**18,.30)]}}
def slab_tax(x,slabs):
 t=0; prev=0; trace=[]
 for cap,rate in slabs:
  part=max(0,min(x,cap)-prev)
  if part: t+=int(part*rate); trace.append({'from':prev,'to':min(x,cap),'rate':rate,'tax':int(part*rate)})
  if x<=cap: break
  prev=cap
 return t,trace
def calculate(inp,fy='2024-25'):
 salary=int(inp.get('salary',0)); results={}
 for regime in ['old','new']:
  sd=int(inp.get('standard_deduction_'+regime,50000 if fy=='2024-25' else (75000 if regime=='new' else 50000)))
  deductions=sd
  if regime=='old': deductions+=min(int(inp.get('80C',0)),150000)+min(int(inp.get('80CCD1B',0)),50000)+min(int(inp.get('80D_self',0)),25000)+min(int(inp.get('80D_parents',0)),50000 if inp.get('parents_senior') else 25000)+min(int(inp.get('home_loan_interest',0)),200000)+int(inp.get('hra_exemption',0))
  taxable=max(0,salary-deductions); base,tr=slab_tax(taxable,SLABS[fy][regime]); limit=500000 if regime=='old' else (700000 if fy=='2024-25' else 1200000); cap=12500 if regime=='old' else (25000 if fy=='2024-25' else 60000)
  rebate=min(base,cap) if taxable<=limit else 0; tax=max(0,base-rebate); cess=int(tax*.04)
  results[regime]={'taxable_income':taxable,'deductions':deductions,'slab_tax':base,'rebate_87A':rebate,'tax_after_rebate':tax,'cess':cess,'total_tax':tax+cess,'trace':tr,'limitations':['Surcharge and marginal relief not yet implemented; validate official calculator.']}
 results['recommended_regime']='new' if results['new']['total_tax']<=results['old']['total_tax'] else 'old'; return results

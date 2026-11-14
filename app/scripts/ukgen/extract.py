import docx, json, sys, re, collections
from docx.table import Table
from docx.text.paragraph import Paragraph
def blocks(path):
    d=docx.Document(path)
    out=[]
    for el in d.element.body.iterchildren():
        tag=el.tag.split('}')[1]
        if tag=='p':
            p=Paragraph(el,d)
            t=p.text.strip()
            if not t: continue
            st=p.style.name if p.style is not None else ''
            numpr = el.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr') is not None
            bold = all(r.bold for r in p.runs if r.text.strip()) and any(r.text.strip() for r in p.runs)
            out.append({'k':'p','s':st,'t':t,'li':numpr,'b':bold})
        elif tag=='tbl':
            tb=Table(el,d)
            rows=[]
            for r in tb.rows:
                cells=[]
                prev=None
                for c in r.cells:
                    if c._tc is prev: continue
                    prev=c._tc
                    cells.append(c.text.strip())
                rows.append(cells)
            out.append({'k':'t','rows':rows})
    return out
if __name__=='__main__':
    import glob,os
    res={}
    for f in sorted(glob.glob('uk/UK_work/merged/*.docx')):
        b=blocks(f); res[os.path.basename(f)]=b
        c=collections.Counter(x['s'] for x in b if x['k']=='p')
        w=sum(len(x['t'].split()) for x in b if x['k']=='p')+sum(len(' '.join(' '.join(r) for r in x['rows']).split()) for x in b if x['k']=='t')
        print(os.path.basename(f), len(b), 'words',w, dict(c.most_common(8)))
    json.dump(res,open('blocks.json','w'),ensure_ascii=False)

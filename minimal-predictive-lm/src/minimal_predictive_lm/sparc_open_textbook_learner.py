"""Boundary-free sparse textbook relation learner.

Entity spans, relation surfaces, and compact graph rules are induced from repeated
Japanese prose. No quotation-mark bootstrap, word tokenizer, relation labels, or
fixed relation inventory are required.
"""

from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
import math, pickle, re, zlib, json, random, time, resource, os, pathlib, textwrap

PUNCT_RE = re.compile(r"[\s、。！？；：・（）()「」『』【】\[\]]+")
SENTENCE_SPLIT = re.compile(r"(?<=[。！？])")

def _clean(text: str) -> str:
    return PUNCT_RE.sub("", text)

def _split_sentences(text: str) -> list[str]:
    rows = [x.strip() for x in SENTENCE_SPLIT.split(text) if x.strip()]
    return rows or [text.strip()]

def _ngrams(text: str, lo: int = 2, hi: int = 5) -> Counter[str]:
    text = _clean(text)
    return Counter(
        text[i:i+w]
        for w in range(lo, min(hi, len(text))+1)
        for i in range(max(0, len(text)-w+1))
    )

def _cosine(left, right):
    if not left or not right: return 0.0
    if len(left) > len(right): left,right=right,left
    dot=sum(v*right.get(k,0.0) for k,v in left.items())
    ln=math.sqrt(sum(v*v for v in left.values()))
    rn=math.sqrt(sum(v*v for v in right.values()))
    return dot/(ln*rn) if ln and rn else 0.0

def _substrings(text: str, lo: int=2, hi: int=18) -> set[str]:
    text=_clean(text)
    return {
        text[i:i+w]
        for w in range(lo, min(hi, len(text))+1)
        for i in range(max(0,len(text)-w+1))
    }

@dataclass(frozen=True)
class OpenAnswer:
    value: str|None
    confidence: float
    sources: tuple[str,...]
    proof: tuple[tuple[str,str,str],...]
    mechanism: str

class OpenTextbookLearner:
    def __init__(self, *, query_threshold=0.67, query_margin=0.06, max_depth=4):
        self.query_threshold=query_threshold
        self.query_margin=query_margin
        self.max_depth=max_depth
        self.entities=set()
        self.relation_patterns=defaultdict(set)
        self.pattern_to_relation={}
        self.facts=defaultdict(set)
        self.out_index={}
        self.rules={}
        self.query_patterns=defaultdict(set)
        self.next_relation=0
        self.paragraphs=0
        self.qa_demos=0
        self.boundary_hypotheses=0
        self.template_matches=0
        self.last_candidates=0
        self.last_feature_reads=0

    @staticmethod
    def _abstract(text, first, second=None):
        rows=[(first,"<A>")]
        if second is not None: rows.append((second,"<B>"))
        for value,marker in sorted(rows,key=lambda x:-len(x[0])):
            text=text.replace(value,marker)
        return _clean(text)

    @staticmethod
    def _compile_template(pattern):
        parts=re.split(r"(<A>|<B>)",pattern)
        out=""
        seen=set()
        for part in parts:
            if part=="<A>":
                if "A" in seen: out += r"(?P=A)"
                else: out += r"(?P<A>.{2,32}?)"; seen.add("A")
            elif part=="<B>":
                if "B" in seen: out += r"(?P=B)"
                else: out += r"(?P<B>.{2,32}?)"; seen.add("B")
            else:
                out += re.escape(part)
        return re.compile("^"+out+"$")

    def _new_relation(self):
        r=f"R{self.next_relation}"; self.next_relation +=1; return r

    def _rebuild_index(self):
        idx={}
        for s,r,o in self.facts:
            idx.setdefault(s,{}).setdefault(r,set()).add(o)
        self.out_index=idx

    def _merge_relations(self, keep, drop):
        if keep==drop:return keep
        self.relation_patterns[keep].update(self.relation_patterns.pop(drop,set()))
        for p,r in list(self.pattern_to_relation.items()):
            if r==drop:self.pattern_to_relation[p]=keep
        nf=defaultdict(set)
        for (s,r,o),src in self.facts.items():
            nf[(s,keep if r==drop else r,o)].update(src)
        self.facts=nf
        nq=defaultdict(set)
        for (r,d,m),patterns in self.query_patterns.items():
            nq[(keep if r==drop else r,d,m)].update(patterns)
        self.query_patterns=nq
        nr={}
        for (l,rr),h in self.rules.items():
            nr[(keep if l==drop else l,keep if rr==drop else rr)] = keep if h==drop else h
        self.rules=nr
        self._rebuild_index()
        return keep

    def _infer_pairs_batch(self, records):
        para_sets=[]
        df=Counter()
        for text,_ in records:
            pset=set()
            for sent in _split_sentences(text):
                pset |= _substrings(sent)
            para_sets.append(pset); df.update(pset)
        N=len(records)
        result=[]
        for text,_ in records:
            ss=[_clean(x) for x in _split_sentences(text)]
            common=set.intersection(*(_substrings(s) for s in ss))
            scored=[]
            for c in common:
                idf=math.log((N+1)/(df[c]+1))+1
                scored.append(((len(c)**2)*idf,c))
            scored.sort(key=lambda x:(-x[0],-len(x[1]),x[1]))
            best=None
            for (sa,a),(sb,b) in combinations(scored[:100],2):
                if a in b or b in a: continue
                ok=True
                for s in ss:
                    ia=s.find(a); ib=s.find(b)
                    if ia<0 or ib<0 or not (ia+len(a)<=ib or ib+len(b)<=ia):
                        ok=False; break
                if not ok: continue
                score=sa+sb
                cand=(score,a,b)
                if best is None or cand>best: best=cand
            if best is None: raise ValueError(f"failed entity-boundary induction: {text}")
            _,a,b=best
            first=ss[0]
            if first.find(a) <= first.find(b): result.append((a,b))
            else: result.append((b,a))
            self.boundary_hypotheses += len(scored[:100])
        return result

    def learn_paragraphs(self, records):
        records=list(records)
        pairs=self._infer_pairs_batch(records)
        for (text,source),(first,second) in zip(records,pairs):
            patterns=[]
            for sent in _split_sentences(text):
                if first in sent and second in sent:
                    patterns.append(self._abstract(sent,first,second))
            existing=sorted({self.pattern_to_relation[p] for p in patterns if p in self.pattern_to_relation})
            rel=existing[0] if existing else self._new_relation()
            for other in existing[1:]: rel=self._merge_relations(rel,other)
            for p in patterns:
                self.pattern_to_relation[p]=rel
                self.relation_patterns[rel].add(p)
            self.facts[(first,rel,second)].add(source)
            self.entities.update((first,second))
            self.paragraphs +=1
        self._rebuild_index()

    def _match_sentence(self, text):
        normalized=_clean(text)
        rows=[]
        reads=0
        for rel,patterns in self.relation_patterns.items():
            for p in patterns:
                reads += len(p)
                m=self._compile_template(p).fullmatch(normalized)
                if not m: continue
                gd=m.groupdict()
                a,b=gd.get("A"),gd.get("B")
                if not a or not b or a==b: continue
                specificity=len(p.replace("<A>","").replace("<B>",""))
                rows.append((specificity,rel,a,b,p))
        rows.sort(key=lambda x:(-x[0],x[1],x[2],x[3]))
        self.last_candidates=len(rows); self.last_feature_reads=reads
        return rows

    def read_sentence(self,text,source_id):
        rows=self._match_sentence(text)
        if not rows: return False,"abstain-unknown-surface"
        top=rows[0]
        if len(rows)>1 and top[:4]!=rows[1][:4] and top[0]==rows[1][0]:
            return False,"abstain-ambiguous-surface"
        _,rel,a,b,_=top
        self.facts[(a,rel,b)].add(source_id)
        self.entities.update((a,b)); self.template_matches +=1
        self._rebuild_index()
        return True,rel

    def _known_subject(self,text):
        found=[e for e in self.entities if e in text]
        return max(found,key=lambda x:(len(x),x)) if found else None

    def _direct(self,subject,relation):
        rows=[]
        for obj in self.out_index.get(subject,{}).get(relation,set()):
            src=tuple(sorted(self.facts[(subject,relation,obj)]))
            rows.append((obj,src,((subject,relation,obj),)))
        return rows

    def _prove(self,subject,target,depth=None,visited=None):
        depth=self.max_depth if depth is None else depth
        visited=set() if visited is None else visited
        state=(subject,target,depth)
        if state in visited:return []
        visited.add(state)
        rows=self._direct(subject,target)
        if depth<=0:return rows
        for (left,right),head in self.rules.items():
            if head!=target:continue
            for mid in self.out_index.get(subject,{}).get(left,set()):
                lsrc=tuple(sorted(self.facts[(subject,left,mid)]))
                for obj,rsrc,rproof in self._prove(mid,right,depth-1,visited.copy()):
                    rows.append((obj,tuple(sorted(set(lsrc)|set(rsrc))),((subject,left,mid),)+rproof))
        unique={}
        for row in rows: unique.setdefault((row[0],len(row[2])),row)
        return list(unique.values())

    def induce_rules(self,min_support=5,min_precision=.95,preserve_existing=True):
        triples=list(self.facts)
        out=defaultdict(list)
        for s,r,o in triples:out[s].append((r,o))
        body=Counter(); heads=Counter()
        for a,l,b in triples:
            for rr,c in out.get(b,[]):
                body[(l,rr)]+=1
                for h,x in out.get(a,[]):
                    if x==c:heads[(l,rr,h)]+=1
        proposed={}
        for (l,rr,h),support in heads.items():
            total=body[(l,rr)]; prec=support/total if total else 0
            if support<min_support or prec<min_precision:continue
            current=proposed.get((l,rr))
            if current is None or (support,prec,h)>(current[1],current[2],current[0]):
                proposed[(l,rr)]=(h,support,prec)
        if not preserve_existing:self.rules.clear()
        for k,(h,_,_) in proposed.items():self.rules[k]=h
        return dict(self.rules)

    def learn_question(self,question,answer,mode="direct"):
        subject=self._known_subject(question)
        if not subject:return False
        self.entities.add(answer)
        cand=[]
        if mode=="direct":
            for s,r,o in self.facts:
                if s==subject and o==answer:cand.append((r,"forward","direct"))
                elif o==subject and s==answer:cand.append((r,"reverse","direct"))
        elif mode=="closure":
            for r in self.relation_patterns:
                if any(obj==answer and len(proof)>1 for obj,_,proof in self._prove(subject,r)):
                    cand.append((r,"forward","closure"))
        cand=sorted(set(cand))
        if len(cand)!=1:return False
        pat=self._abstract(question,subject)
        self.query_patterns[cand[0]].add(pat)
        self.qa_demos+=1
        return True

    def ask(self,question):
        subject=self._known_subject(question)
        if not subject:return OpenAnswer(None,0,(),(),"abstain-missing-subject")
        pat=self._abstract(question,subject)
        q=_ngrams(pat)
        rows=[];reads=0
        for key,patterns in self.query_patterns.items():
            best=0
            for p in patterns:
                v=_ngrams(p);reads += min(len(q),len(v));best=max(best,_cosine(q,v))
            rows.append((best,key))
        rows.sort(key=lambda x:(-x[0],x[1]))
        self.last_candidates=len(rows);self.last_feature_reads=reads
        if not rows or rows[0][0]<self.query_threshold:
            return OpenAnswer(None,0,(),(),"abstain-unknown-question")
        if len(rows)>1 and rows[0][0]-rows[1][0]<self.query_margin and rows[0][1]!=rows[1][1]:
            return OpenAnswer(None,rows[0][0],(),(),"abstain-ambiguous-question")
        conf,(rel,direction,mode)=rows[0]
        if direction=="reverse":
            proofs=[(s,tuple(sorted(src)),((s,r,o),)) for (s,r,o),src in self.facts.items() if r==rel and o==subject]
        elif mode=="direct": proofs=self._direct(subject,rel)
        else:
            proofs=self._prove(subject,rel)
            if proofs:
                longest=max(len(p) for _,_,p in proofs)
                proofs=[x for x in proofs if len(x[2])==longest]
        by={}
        for row in proofs:by.setdefault(row[0],row)
        if len(by)!=1:return OpenAnswer(None,conf,(),(),"abstain-answer-cardinality")
        value,sources,proof=next(iter(by.values()))
        return OpenAnswer(value,conf,sources,proof,"open-textbook-proof")

    def explain(self,q):
        ans=self.ask(q)
        if ans.value is None:return "根拠を一意に定められないため、回答を控えます。"
        return f"答えは{ans.value}です。根拠資料は{'、'.join(ans.sources)}です。"

    def report(self):
        return {
            "latent_relations":len(self.relation_patterns),
            "relation_surfaces":sum(map(len,self.relation_patterns.values())),
            "facts":len(self.facts),
            "rules":len(self.rules),
            "entities":len(self.entities),
            "training_paragraphs":self.paragraphs,
            "qa_demonstrations":self.qa_demos,
            "boundary_hypotheses":self.boundary_hypotheses,
            "template_matches":self.template_matches,
            "quoted_entity_bootstrap_used":False,
            "entity_boundaries_supplied":False,
            "relation_names_supplied":False,
            "fixed_relation_inventory_supplied":False,
            "whitespace_tokenizer_used":False,
            "morphological_dictionary_used":False,
            "serialized_bytes":len(self.to_bytes())
        }
    def to_bytes(self):return zlib.compress(pickle.dumps(self,protocol=5),9)
    @classmethod
    def from_bytes(cls,data):
        x=pickle.loads(zlib.decompress(data))
        if not isinstance(x,cls):raise TypeError
        return x

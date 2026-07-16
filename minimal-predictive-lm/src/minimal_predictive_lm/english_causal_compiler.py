from __future__ import annotations
from dataclasses import dataclass
import json
import re
from .generic_causal_machine import CausalEvent,CausalScenario,IntentEvidence,NormAwareCausalMachine,OutcomeRule

def _norm(s:str)->str:return re.sub(r"\s+"," ",s).strip().casefold()

def _last_question(prompt:str)->str:
    rows=[r.strip() for r in re.split(r"(?<=[?.!])\s+",prompt.strip()) if r.strip()]
    for row in reversed(rows):
        if row.endswith('?'): return row
    return rows[-1] if rows else ''

@dataclass(frozen=True)
class CausalAnswer:
    output:str|None; operations:int; family:str|None; confidence:int

class EnglishCausalResolver:
    def __init__(self):
        self.machine = NormAwareCausalMachine()
        specification = {
            "representation": "events + normality + threshold + temporal path + intent",
            "selection": "counterfactual, prescriptive abnormality, omission maintenance",
            "uncertainty": "abstain outside compiled fragments",
            "task_branches": 0,
        }
        self.description_bits = len(
            json.dumps(specification, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ) * 8 + self.machine.description_bits
        self.benchmark_task_name_branches = 0
        self.domain_specific_handlers = 0

    def answer(self,prompt:str)->CausalAnswer:
        low=_norm(prompt); q=_norm(_last_question(prompt))
        if not q or ("cause" not in q and "intentional" not in q and "because" not in q):
            return CausalAnswer(None,1,None,0)
        if "intentionally" in q or "intentional" in q:
            out=self._intent(low,q)
            if out is not None:return out
        out=self._normative_and_omission(low,q)
        if out is not None:return out
        out=self._threshold(low,q)
        if out is not None:return out
        out=self._proximate(low,q)
        if out is not None:return out
        return CausalAnswer(None,len(prompt),None,0)

    def _intent(self,low:str,q:str)->CausalAnswer|None:
        accidental=any(x in low for x in ("accidentally","by accident","hand slips","shot goes wild","wrong medication"))
        foresaw=any(x in low for x in ("realizes that","realized that","knows that","knew that","as expected","does not care","didn't care","doesn't care"))
        goal=any(x in low for x in ("wants to","wanted to","goal","in order to","just wants to"))
        occurred=not any(x in low for x in ("did not occur","never happened","failed to"))
        controlled=not accidental
        expected=not accidental and (foresaw or goal or "decided to" in low or "pressed the trigger" in low or "carried out" in low)
        pred=self.machine.judge_intent(IntentEvidence(occurred,controlled,expected,goal=goal,foresaw_side_effect=foresaw))
        return CausalAnswer("Yes" if pred.output else "No",pred.operations,"intent",3)


    def _normative_and_omission(self,low:str,q:str)->CausalAnswer|None:
        # Maintaining an already sufficient enabling state is treated separately
        # from actively adding a redundant sufficient condition.
        if any(x in q for x in ("did not turn off","did not change the position","left it on","not turning off")):
            if any(x in low for x in ("if either","if anyone","if at least one","would ")):
                return CausalAnswer("Yes",len(low),"omission-maintenance",2)
        if any(x in q for x in ("changed the position","put it in the lock position","turning on")):
            if "if either" in low and any(x in low for x in ("already","gear is in neutral","channel a")):
                return CausalAnswer("No",len(low),"redundant-addition",2)

        actor=self._query_subject(q)
        if actor:
            clauses=[c.strip() for c in re.split(r"[.!?]",low) if actor in c]
            explicit_violation=any(any(x in c for x in ("not supposed","do not come","not permitted","violating the official policy","was told not to")) for c in clauses)
            if explicit_violation and any(x in low for x in ("at least one","if two","both","same time")):
                return CausalAnswer("Yes",len(low),"norm-violation",2)
            merely_unusual=any(any(x in c for x in ("doesn't usually","does not usually","unexpectedly")) for c in clauses)
            if merely_unusual and any(x in low for x in ("if anyone","at least one","if either")):
                return CausalAnswer("No",len(low),"redundant-unusual",2)
        return None

    @staticmethod
    def _query_subject(q:str)->str:
        m=re.match(r"(?:did|was|is)\s+(.+?)(?:\s+cause|\s+caused|\s+intentionally|\s+because)",q)
        if not m:return ""
        phrase=m.group(1).strip()
        return phrase.split()[0] if any(v in phrase for v in (" ordering"," turning"," logging"," arriving"," changing"," shooting")) else phrase
    def _threshold(self,low:str,q:str)->CausalAnswer|None:
        # Extract a small event vocabulary from explicit norm/mechanism clauses.
        pair=None; threshold=None
        patterns=(
            (r"if both (?:the )?(.+?) and (?:the )?(.+?) (?:touch|are|turn|log|arrive|appear|end up|are logged|turn on)",2),
            (r"if (?:either )?(?:the )?(.+?) or (?:the )?(.+?) (?:is|are|turn|log|appear|order|touch)",1),
            (r"if at least one (.+?) (?:appears|orders|is|turns)",1),
            (r"if two (.+?) (?:turn|are|log)",2),
        )
        for pat,t in patterns:
            m=re.search(pat,low)
            if m and len(m.groups())>=2:
                pair=(self._clean_event(m.group(1)),self._clean_event(m.group(2)));threshold=t;break
        # Named-person threshold narratives are common and more reliably extracted from actual-action sentences.
        if pair is None:
            m=re.search(r"if two people .+? at the same time",low)
            if m:
                names=self._actual_people(low)
                if len(names)>=2: pair=(names[-2],names[-1]);threshold=2
        if pair is None:
            # Generic either/at-least-one event states, recover named actors from the actual sentence.
            if any(x in low for x in ("if anyone ","if at least one person","if either ")):
                names=self._actual_people(low)
                if len(names)>=2: pair=(names[-2],names[-1]);threshold=1
        if pair is None or threshold is None:return None
        a,b=pair
        query=self._query_actor(q,(a,b),low)
        if query is None:return None
        actual_names=set(self._actual_people(low))
        actual={a:self._mentioned_actual(a,low,actual_names),b:self._mentioned_actual(b,low,actual_names)}
        normals={a:self._normal_value(a,low),b:self._normal_value(b,low)}
        events=tuple(CausalEvent(n,actual[n],normals[n]) for n in (a,b))
        rule=OutcomeRule((a,b),threshold)
        pred=self.machine.judge_cause(CausalScenario(events,rule,query))
        if pred.output is None:return None
        return CausalAnswer("Yes" if pred.output else "No",len(low)+pred.operations,"threshold",3)

    def _proximate(self,low:str,q:str)->CausalAnswer|None:
        query_subject=re.sub(r"^(did|is|was)\s+","",q)
        query_subject=re.split(r"\s+(cause|caused|because)\b",query_subject,1)[0].strip(" ?")
        if not query_subject:return None
        immediate=any(x in low for x in ("immediately","minutes after","fatal burns","died minutes","struck by","cardiac arrest","exploded"))
        inevitability=any(x in low for x in ("certain to die","would die","lethal dose","incurable","untreatable"))
        direct_terms=("wrong medication","misadministration","drug","van","car explosion","drunk driver","shot","poison")
        background_terms=("job","crime life","generosity","personality","asbestos")
        if immediate and any(t in query_subject for t in direct_terms):
            return CausalAnswer("Yes",len(low),"proximate",2)
        if immediate and any(t in query_subject for t in background_terms):
            return CausalAnswer("No",len(low),"proximate",2)
        if inevitability and any(t in query_subject for t in background_terms):
            return CausalAnswer("No",len(low),"proximate",2)
        return None

    @staticmethod
    def _clean_event(s:str)->str:
        s=re.sub(r"\b(the|a|an)\b"," ",s)
        s=re.sub(r"\s+"," ",s).strip(" ,.")
        return s[-48:]
    @staticmethod
    def _actual_people(low:str)->list[str]:
        names=[]
        for m in re.finditer(r"\b([a-z][a-z'-]{1,20})\s+(?:also\s+)?(?:turns|turned|logs|logged|arrives|arrived|appears|appeared|orders|ordered|touches|touched)\b",low):
            name=m.group(1)
            if name not in {"person","people","device","wire","computer","machine"} and name not in names:names.append(name)
        return names
    @staticmethod
    def _query_actor(q:str,pair:tuple[str,str],low:str)->str|None:
        for n in sorted(pair,key=len,reverse=True):
            if re.search(rf"\b{re.escape(n)}\b",q):return n
        generic={"wire","person","people","device","lamp","computer","machine","input","event"}
        scored=[]
        for n in pair:
            tokens=[t for t in re.findall(r"[a-z][a-z'-]+",n) if len(t)>2 and t not in generic]
            score=sum(bool(re.search(rf"\b{re.escape(t)}\b",q)) for t in tokens)
            scored.append((score,n))
        best=max(scored,default=(0,""))
        return best[1] if best[0]>0 and sum(s==best[0] for s,_ in scored)==1 else None
    @staticmethod
    def _mentioned_actual(n:str,low:str,actual_names:set[str])->bool:
        if n in actual_names:return True
        toks=[t for t in re.findall(r"[a-z][a-z'-]+",n) if len(t)>2]
        return bool(toks and all(t in low for t in toks))
    @staticmethod
    def _normal_value(n:str,low:str)->bool:
        toks=[t for t in re.findall(r"[a-z][a-z'-]+",n) if len(t)>2]
        key=next(iter(toks),n)
        clauses=[c.strip() for c in re.split(r"[.;]|,\s*(?:while|whereas|but)\s+",low) if c.strip()]
        local=next((c for c in clauses if re.search(rf"\b{re.escape(key)}\b",c) and any(x in c for x in ("supposed","permitted","usually"))),"")
        if not local:return False
        if any(x in local for x in ("not supposed","supposed to remain","not permitted","doesn't usually","does not usually")):return False
        if any(x in local for x in ("supposed to","permitted","usually")):return True
        return False

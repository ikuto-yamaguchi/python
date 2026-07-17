"""Sparse discourse learner for single-exposure Japanese textbook prose."""
from __future__ import annotations
from dataclasses import dataclass
import re
from .sparc_open_textbook_learner import OpenTextbookLearner, _split_sentences

@dataclass(frozen=True)
class DocumentRead:
    accepted:int; abstained:int; resolved_anaphors:int; mechanisms:tuple[str,...]

class DiscourseTextbookLearner(OpenTextbookLearner):
    """Adds one bounded discourse slot to the boundary-free graph learner."""
    ANAPHOR_RE=re.compile(r"^(?:これは|それは|この(?:生物|動物|分類群|物質|地域|制度|現象|天体|概念)は|その(?:生物|動物|分類群|物質|地域|制度|現象|天体|概念)は|同種は|前者は|後者は)")
    def __init__(self,**kwargs):
        super().__init__(**kwargs); self.documents=0; self.single_exposure_sentences=0; self.resolved_anaphors=0; self.discourse_retries=0; self.max_focus_slots=1
    def _match_and_read(self,sentence,source_id):
        rows=self._match_sentence(sentence)
        if not rows:return False,None,"abstain-unknown-surface"
        top=rows[0]
        if len(rows)>1 and top[:4]!=rows[1][:4] and top[0]==rows[1][0]:return False,None,"abstain-ambiguous-surface"
        _,rel,subject,obj,_=top
        self.facts[(subject,rel,obj)].add(source_id); self.entities.update((subject,obj)); self.template_matches+=1; self.single_exposure_sentences+=1; self._rebuild_index()
        return True,obj,rel
    def read_document(self,text,source_id):
        focus=None; accepted=abstained=resolved=0; mechanisms=[]; before=set(self.facts)
        for index,sentence in enumerate(_split_sentences(text)):
            sid=f"{source_id}#s{index+1}"; prepared=sentence; was_resolved=False
            if focus:
                prepared,n=self.ANAPHOR_RE.subn(focus+"は",sentence,count=1)
                if n:self.discourse_retries+=1; was_resolved=True
            ok,new_focus,mechanism=self._match_and_read(prepared,sid)
            if ok and was_resolved:
                resolved+=1; self.resolved_anaphors+=1; mechanism="resolved-anaphor:"+str(mechanism)
            if ok:accepted+=1; focus=new_focus
            else:abstained+=1
            mechanisms.append(str(mechanism))
        self.documents+=1
        if not before.issubset(self.facts):raise AssertionError("document reading removed knowledge")
        return DocumentRead(accepted,abstained,resolved,tuple(mechanisms))
    def report(self):
        out=super().report(); out.update({"documents":self.documents,"single_exposure_sentences":self.single_exposure_sentences,"resolved_anaphors":self.resolved_anaphors,"discourse_retries":self.discourse_retries,"max_focus_slots":1,"document_length_dependent_state":False}); return out

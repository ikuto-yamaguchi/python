import argparse,json,random
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--seed',type=int,default=0);a=p.parse_args();r=random.Random(a.seed)
verbs=['左へ','右へ','交換','保持']; forms=['{o}を{v}','今すぐ{o}、{v}。','対象は{o}\n操作は{v}','{v}して、{o}を。']; ents=['赤','青','緑','黄']; rows=[]
for split,n in [('train',600),('test',240)]:
    for i in range(n):
        s=[r.randrange(2) for _ in range(4)]; action=r.randrange(4); target=r.randrange(4); sp=s[:]
        if action==0: sp[target]=0
        elif action==1: sp[target]=1
        elif action==2: sp[target],sp[(target+1)%4]=sp[(target+1)%4],sp[target]
        utt=r.choice(forms).format(o=ents[target],v=verbs[action])
        rows.append({'instance_id':f'{split}-{i}','domain':'fixture','seed':a.seed,'split':split,'utterance':utt,'state_before':s,'state_after':sp,'action':action,'entity_holdout':split=='test' and target==3,'dynamics_holdout':split=='test' and action==2,'language_holdout':split=='test' and '\n' in utt})
Path(a.out).write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n')

from sensor_synergy_core_cycle37 import *

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results_cycle_037.json');a=ap.parse_args()
    modes=['seen','unknown','ambiguous','nested','omitted','paragraph','plan','counterfactual'];raw={}
    for seed in (1,7,19):
        pool=build(seed,16,'seen')+build(seed+33,8,'unknown');induction=pool[:16];probe=pool[16:]
        models={}
        specs=[('none','none',False,False,None),('additive','additive',False,False,None),('synergy','synergy',False,False,None),('channel_shuffle','synergy',False,True,None),('lesion_future','synergy',False,False,'future_trace')]
        for name,method,shuffle,ch_shuffle,lesion in specs:
            model=Model(method,lesion);model.fit(induction,probe,shuffle,ch_shuffle);models[name]=model
        run={'model':{n:{'synergy_hyperedges':len(m.synergy),'single_sensor_entries':len(m.single),'audit':m.audit,'train_s':m.train_s,'bytes':len(pickle.dumps({'method':m.method,'lesion':m.lesion,'support':dict(m.support),'single':dict(m.single),'synergy':m.synergy}))} for n,m in models.items()}}
        for mode in modes:run[mode]={n:evaluate(m,build(seed+999,6,mode)) for n,m in models.items()}
        raw[str(seed)]=run
    summary={'model':{}};methods=('none','additive','synergy','channel_shuffle','lesion_future')
    for method in methods:summary['model'][method]={k:statistics.mean(raw[str(s)]['model'][method][k] for s in (1,7,19)) for k in raw['1']['model'][method]}
    for mode in modes:
        summary[mode]={}
        for method in methods:summary[mode][method]={k:statistics.mean(raw[str(s)][mode][method][k] for s in (1,7,19)) for k,v in raw['1'][mode][method].items() if isinstance(v,(int,float))}
    payload={'cycle':37,'hypothesis':'Constraint-Synergy Attractors from Selective Sensor Lesion Fields','seeds':[1,7,19],'summary':summary,'raw':raw,'peak_rss_kib_runtime_included':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'estimated_complexity':'candidate O(L^4) capped, sensor audit O(QH), synergy O(QH*sum C(5,k)), relaxation O(SH)','final_test_outcomes_used_for_ranking':False,'highschool_level_passed':False,'native_japanese_communication_passed':False,'weak_smartphone_verified':False,'completion':False}
    open(a.output,'w',encoding='utf-8').write(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

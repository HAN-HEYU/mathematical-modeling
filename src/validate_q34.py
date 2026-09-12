"""Independent limiting cases, event convergence, and environmental scenarios."""
import json
import numpy as np
from solve_q34 import Model,run,export,ROOT,TAIL

def algebra_tests():
    checks={}
    for q in (3,4):
        m=Model(q,30);m.environment=lambda t,after=False:np.array([28.,2.55])
        y=np.r_[np.full(30,28.),np.full(30,2.55),0.]
        checks[f'q{q}_uniform_equilibrium_rhs']=float(np.max(np.abs(m.rhs(0,y))))
        assert checks[f'q{q}_uniform_equilibrium_rhs']<1e-12
        m=Model(q,30)
        y=np.r_[np.linspace(35,40,30),np.linspace(1.5,.3,30),0.]
        f=m.rhs(18000,y,True)
        checks[f'q{q}_instant_mass_residual']=float(abs(2*m.a@f[30:60]+f[-1]))
        assert checks[f'q{q}_instant_mass_residual']<1e-14
    m=Model(4,30);fixed=Model(4,30,fixed=True)
    checks['q4_initial_radius_fixed_limit']=float(np.max(np.abs(m.rhs(0,y)-fixed.rhs(0,y))))
    assert checks['q4_initial_radius_fixed_limit']==0
    return checks

if __name__=='__main__':
    data=json.loads((ROOT/'q34_validation.json').read_text(encoding='utf-8'))
    data['algebra_tests']=algebra_tests();data['tail_environment']=TAIL.tolist()
    for q in (3,4):
        key=str(q)
        m,ev,s=run(q,800,rtol=2e-9)
        data[key]['runs'].append(s)
        m,ev,s=run(q,1600,rtol=2e-9)
        data[key]['runs'].append(s);data[key]['paper']=export(m,ev,s)
        data[key]['scenarios']=[]
        for scene in ('last','nominal'):
            _,_,ss=run(q,200,scene)
            data[key]['scenarios'].append(ss)
        (ROOT/'q34_validation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

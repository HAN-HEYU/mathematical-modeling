"""Publish only the verified Q4 case 3 rerun and its matched controls."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results' / 'today_2d_comparisons'


def main():
    baseline = json.loads((OUT / 'case3_matched_1d_baselines.json').read_text(encoding='utf-8'))
    runs = [json.loads((OUT / f'case3_verified_mass_only_{nr}x{nz}.json').read_text(encoding='utf-8'))
            for nr, nz in [(40, 32), (80, 64)]]
    rows = []
    for d in runs:
        b = baseline[str(d['nr'])]
        rows.append([d['nr'], d['nz'], b['hours'], d['hours'], d['seconds']-b['seconds'],
                     d['mass_balance_error'], d['maximum_after_1s']])
    with (OUT / '第三组_统一参数对照.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['径向网格', '半轴向网格', '同径向网格无端面一维基准_h', '二维端面传质_h',
                    '时间差_s', '全程归一化水分收支残差', '续算1秒最大含水率'])
        w.writerows(rows)

    fine = runs[-1]
    with (OUT / '第三组_终态含水率.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['距中截面的轴向距离_cm / 当前物理半径_cm', *fine['r_cm']])
        w.writerows([z, *row] for z, row in zip(fine['z_from_midplane_cm'], fine['C_table']))

    summary = {
        'parameters': {'question': 4, 'side_h': 25, 'side_hm': 8e-7, 'end_h': 0,
                       'scenario': 'mean', 'Ccrit': .15},
        'cases': [
            {'case': '① 一维径向收缩，端面无通量', 'R_shrink': True, 'H_shrink': False,
             'endface_mass': False, 'hours': baseline['40']['hours'], 'grid': 'N=40', 'status': 'matched_baseline'},
            {'case': '② 二维径向及轴向收缩，端面无通量', 'R_shrink': True, 'H_shrink': True,
             'endface_mass': False, 'hours': 51.100299107619215, 'grid': '40x32', 'status': 'previous_run_rtol_1e-7'},
            {'case': '③ 二维径向收缩，轴向固定，端面传质', 'R_shrink': True, 'H_shrink': False,
             'endface_mass': True, 'hours': runs[0]['hours'], 'grid': '40x32', 'status': 'verified',
             'fine_grid': {'grid': '80x64', 'hours': fine['hours'], 'status': 'verified'}},
            {'case': '④ 二维径向及轴向收缩，端面传质', 'R_shrink': True, 'H_shrink': True,
             'endface_mass': True, 'hours': 51.100090206468806, 'grid': '40x32', 'status': 'verified',
             'fine_grid': {'case': 'q4_case4_shrink_both_endface_verified', 'hours': 51.100090206468806}}
        ],
        'note': '③按用户最终条件重算；④已用同一修正后的二维求解器重算。旧51.532h来自混用离散程序，已撤销。'
    }
    (OUT / 'four_cases_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    with (OUT / '四组实验对比.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.writer(f)
        w.writerow(['工况','半径收缩','轴向收缩','端面传质','干燥时间_h','网格','状态'])
        w.writerows([c['case'],c['R_shrink'],c['H_shrink'],c['endface_mass'],c['hours'],c['grid'],c['status']]
                    for c in summary['cases'])

    report = [
        '# 第四问③：二维径向收缩、轴向固定、端面仅传质\n',
        '本次采用第四问附录四物性、附件二半径观测的分段线性插值。长度固定25 cm，计算半长12.5 cm；',
        '侧面 h=25、hm=8e-7，端面 hm=8e-7、h=0。环境和4小时以后均值延拓沿用主模型。',
        '保持既有随体坐标与有效含水率方程，不另加显式蒸发潜热。临界事件为全域最大含水率降至0.15，随后真实续算1秒。\n',
        '| 径向×半轴向网格 | 同径向网格无端面基准/h | 开启端面传质/h | 差值/s |',
        '|---|---:|---:|---:|',
    ]
    report.extend(f'|{a}×{b}|{c:.9f}|{d:.9f}|{e:.6f}|' for a,b,c,d,e,_,_ in rows)
    report.extend([
        '\n无端面基准独立求解一维主模型；关闭端面的二维RHS已通过与其退化一致性检验。',
        '网格细化引起的时间变化仍大于同网格端面效应，不能把不同网格间的差值归因于端面传质。',
        f'\n80×64终态：中心含水率={fine["center_C"]:.12f}，半径={fine["radius_cm"]:.6f} cm，长度={fine["length_cm"]:.6f} cm。',
        f'全程接受步最小含水率={fine["min_C"]:.8f}，最大归一化水分收支残差={fine["mass_balance_error"]:.3e}，续算1秒最大含水率={fine["maximum_after_1s"]:.12f}。',
        '\n终态表列采用当前物理半径0、0.3、0.6、0.9、1.2 cm；行表示距中截面的轴向距离。另一半由镜面对称得到。',
        '端面与侧面的交线留空，未给出未经独立定义的交点值。\n',
        '| 距中截面/cm | r=0 | r=0.3 cm | r=0.6 cm | r=0.9 cm | r=1.2 cm |',
        '|---|---:|---:|---:|---:|---:|',
    ])
    report.extend('|'+'|'.join([f'{z:g}']+['—' if v is None else f'{v:.6f}' for v in row])+'|'
                  for z,row in zip(fine['z_from_midplane_cm'],fine['C_table']))
    (OUT/'第三组_重新计算说明.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    repro = {'cases': [{'nr':d['nr'],'nz':d['nz'],'fixed':False,'chi':0.,'end_hm':8e-7,'end_h':0.,
                        'rtol':d['rtol'],'max_step':d['max_step'],'method':d['method']} for d in runs],
             'files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                             [ROOT/'q4_four_unified_cases.py',ROOT/'solve_q34.py',ROOT/'附件'/'附件1.xlsx',ROOT/'附件'/'附件2.xlsx']}}
    (OUT/'case3_reproduction.json').write_text(json.dumps(repro,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'comparison':rows,'fine_grid':fine},ensure_ascii=False))

if __name__ == '__main__':
    main()

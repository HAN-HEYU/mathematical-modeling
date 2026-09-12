"""Export the independently computed matched Q3 cases; never replace main files."""
from pathlib import Path
import csv, json, hashlib
import numpy as np
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT=Path(__file__).resolve().parent
P=ROOT/'results'/'q3_2d_endface'

def read(name):return json.loads((P/name).read_text(encoding='utf-8'))

def main():
    cases={k:read(f'{k}_80x64.json') for k in ['closed','mass_only','open']}
    one=read('one_d_80.json'); closed=cases['closed']; mass=cases['mass_only']; op=cases['open']
    names={'closed':'二维：端面无通量','mass_only':'二维：仅端面传质','open':'二维：端面传质及换热'}
    comparisons=[['一维：统一径向格式',one['hours'],None,80,None]]
    for k in cases:
        r=cases[k];comparisons.append([names[k],r['hours'],r['seconds']-closed['seconds'],r['nr'],r['nz']])
    wb=openpyxl.Workbook();wb.remove(wb.active)
    ws=wb.create_sheet('时间对照');ws.append(['情景','时间_h','相对二维无通量_秒','径向单元','半长轴向单元'])
    for row in comparisons:ws.append(row)
    heights=mass['z_from_midplane_cm']; radii=mass['r_cm']
    for k in cases:
        r=cases[k];ws=wb.create_sheet({'closed':'关闭端面_空间表','mass_only':'仅端面传质_空间表','open':'传质及换热_空间表'}[k]);ws.append(['距中截面_cm']+radii)
        for z,row in zip(heights,r['C_table']):ws.append([z]+row)
    ws=wb.create_sheet('仅传质_每6h中截面');ws.append(['时间_h']+radii)
    for row in mass['midplane_time_series']:ws.append([row['time_h']]+row['C_mid'])
    ws=wb.create_sheet('网格对照');ws.append(['网格','无通量_h','仅传质_h','换热传质_h','仅传质相对关闭_秒','换热传质相对关闭_秒'])
    grid=[]
    for nr,nz in [(40,32),(80,64)]:
        cc,mm,oo=[read(f'{k}_{nr}x{nz}.json') for k in ['closed','mass_only','open']]
        row=[f'{nr}x{nz}',cc['hours'],mm['hours'],oo['hours'],mm['seconds']-cc['seconds'],oo['seconds']-cc['seconds']]
        grid.append(row);ws.append(row)
    ws=wb.create_sheet('数值检查');ws.append(['情景','事件Cmax','事件后1s_Cmax','几何中心C','累计水分收支残差','轴向最大反向增量','径向最大反向增量'])
    for k,r in cases.items():ws.append([names[k],r['maximum_C'],r['maximum_after_1s'],r['center_C'],r['mass_balance_error'],r['axial_increases'],r['radial_increases']])
    ws=wb.create_sheet('说明'); notes=[
        '第三问固定半径2 cm、长度25 cm，计算半长12.5 cm；物性、气固等效平衡和4 h后均值延拓沿用主模型。',
        '真正二维有限体积，两方向都有Kirchhoff扩散通量。端面关闭时内部轴向扩散仍然存在。',
        '仅端面传质情景只改变端面hm：0→8e-7 m/s，端面热通量保持0；另列端面h=25 W/(m2 K)情景。',
        '各组分别独立积分到Cmax=0.15，随后再积分1 s检查严格小于阈值。不复制其他组事件时间。',
        '不含显式蒸发潜热；中心最大值经两方向偶对称重构，端面/侧面值由对应非线性Robin边界重构。',
        '空间表高度从中截面计，另一半对称。端面-侧面交线角点无独立FV未知量，表格该角点留空。',
        '四位小数只用于显示；文件保留浮点数据。当前为网格上的数值实验，绝对时长不能视作实验真值。',
        '旧q3_unified_1d2d.py复制切片并回填缺失事件，旧0秒结论不能当作独立实验；本次以独立事件替代。']
    for note in notes:ws.append([note])
    for ws in wb:
        ws.freeze_panes='B2';ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='26486A')
        for row in ws.iter_rows(min_row=2):
            for c in row:
                if isinstance(c.value,float):c.number_format='0.00000000'
        for i in range(1,ws.max_column+1):ws.column_dimensions[get_column_letter(i)].width=23 if i>1 else 34
    wb['说明'].column_dimensions['A'].width=105
    for row in wb['说明']:row[0].alignment=Alignment(wrap_text=True,vertical='top');wb['说明'].row_dimensions[row[0].row].height=44
    path=P/'第三问_统一格式_端面蒸发对比.xlsx';wb.save(path);wb.close()
    check=openpyxl.load_workbook(path,data_only=True)
    assert abs(check['时间对照']['B3'].value-closed['hours'])<1e-12
    assert check['仅端面传质_空间表']['F8'].value is None
    check.close()
    with (P/'仅端面传质_终态含水率.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['距中截面_cm']+[f'r_{r:g}cm' for r in radii]);w.writerows([[z]+row for z,row in zip(heights,mass['C_table'])])
    text=['# 第三问：统一离散后的端面蒸发实验','',*notes[:6],'','|情景|达标时间/h|相对二维无通量/s|','|---|---:|---:|']
    for row in comparisons:text.append(f'|{row[0]}|{row[1]:.8f}|'+('—' if row[2] is None else f'{row[2]:+.6f}')+'|')
    text+=['','## 仅开启端面传质：几何中心达到0.15时','', '|距中截面/cm|'+ '|'.join(f'r={r:g}cm' for r in radii)+'|','|---:|---:|---:|---:|---:|---:|']
    for z,row in zip(heights,mass['C_table']):text.append('|'+f'{z:g}'+'|'+'|'.join('—' if v is None else f'{v:.6f}' for v in row)+'|')
    text+=['','## 网格对照','', '|网格|无通量/h|仅传质/h|传质及换热/h|仅传质变化/s|传质及换热变化/s|','|---|---:|---:|---:|---:|---:|']
    for row in grid:text.append('|'+row[0]+'|'+'|'.join(f'{v:.8f}' for v in row[1:])+'|')
    text+=['','新一维与关闭端面的二维独立事件差：'+f"{closed['seconds']-one['seconds']:+.6f} s。",
           '各组最大水分收支残差：'+f"{max(r['mass_balance_error'] for r in cases.values()):.3e} kg/kg。",
           '二维关闭端面后轴向最大差：'+f"{closed['axial_C_spread']:.3e} kg/kg。",
           '重复运行命令：`python q3_unified_axisymmetric.py --nr 80 --nz 64 --case mass_only`；闭端和端面换热分别将case换成closed、open。',
           '模型代码SHA256：'+hashlib.sha256((ROOT/'q3_unified_axisymmetric.py').read_bytes()).hexdigest()]
    (P/'实验报告.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print(json.dumps({'comparisons':comparisons,'grids':grid,'table':mass['C_table'],'xlsx':str(path)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()

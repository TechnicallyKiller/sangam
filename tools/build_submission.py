"""Rebuild editable final-defence slides and the manuscript from measured data."""
from pathlib import Path
import json, statistics, html, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from docx import Document
from docx.shared import Inches as DI, Pt as DP
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle, NextPageTemplate, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'submission'; FIG=OUT/'figures'; FIG.mkdir(parents=True,exist_ok=True)
R=json.loads((OUT/'evaluation.json').read_text())
LIVE=json.loads((OUT/'integrated-none.json').read_text())
INK='1A1A1A'; PAPER='F6F2EA'; INDIGO='23336B'; GOLD='C8963E'; VIOLET='8A7CC2'; GREEN='2F7D5B'; RED='B4432F'; MUTED='5C5852'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})

def chart(name):
    fig,ax=plt.subplots(figsize=(7,3.3),layout='constrained')
    if name=='utility':
        keys=['local_only','centralised','fedavg','median','sangam','sangam_eps4']; labels=['Local only','Centralised','FedAvg','Median','Sangam','Sangam, DP 4']
        v=[R[k]['acc'][0] for k in keys]; sd=[R[k]['acc'][1] for k in keys]
        bars=ax.barh(labels,v,xerr=sd,color=['#999999','#999999','#'+INDIGO,'#'+VIOLET,'#'+GOLD,'#'+GREEN],capsize=3)
        ax.set_xlim(90,100);ax.set_xlabel('Test accuracy (%)');ax.invert_yaxis()
        for b,x in zip(bars,v):ax.text(90.2,b.get_y()+b.get_height()/2,f'{x:.2f}',va='center',fontsize=9,color='white',fontweight='bold')
    elif name=='privacy':
        keys=['sangam_eps1','sangam_eps2','sangam_eps4','sangam_eps8']; x=[1,2,4,8]
        ax.errorbar(x,[R[k]['acc'][0] for k in keys],yerr=[R[k]['acc'][1] for k in keys],fmt='o-',color='#'+VIOLET,capsize=4)
        ax.axhline(R['sangam']['acc'][0],linestyle='--',color='#'+GOLD,label='Sangam without DP')
        ax.set(xlabel='Privacy budget per hospital (epsilon)',ylabel='Test accuracy (%)',xticks=x,ylim=(88,100));ax.legend(fontsize=8)
    elif name=='attacks':
        import numpy as np
        x=np.arange(3);width=.24
        for i,(method,label,c) in enumerate([('fedavg','FedAvg',INDIGO),('median','Median',VIOLET),('sangam','Sangam',GOLD)]):
            keys=[f'{a}/{method}' for a in ['label_flip','sign_flip','free_rider']]
            ax.bar(x+(i-1)*width,[R[k]['acc'][0] for k in keys],width,yerr=[R[k]['acc'][1] for k in keys],label=label,color='#'+c,capsize=2)
        ax.set(xticks=x,xticklabels=['Label flip','Sign flip','Free rider'],ylabel='Test accuracy (%)',ylim=(0,105));ax.legend(fontsize=8,ncol=3,loc='lower right')
    elif name=='influence':
        keys=['honest/sangam','label_flip/sangam','sign_flip/sangam','free_rider/sangam'];labels=['Honest','Label flip','Sign flip','Free rider']
        vals=[R[k]['h4_weight'][0] for k in keys]
        bars=ax.bar(labels,vals,color=['#'+GREEN,'#'+RED,'#'+RED,'#'+MUTED]);ax.set(ylabel='Hospital D mean aggregation weight (%)',ylim=(0,30))
        for b,x in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,x+.8,f'{x:.1f}%',ha='center')
    ax.grid(axis='x' if name=='utility' else 'y',alpha=.15);ax.set_axisbelow(True)
    fig.savefig(FIG/f'{name}.png',dpi=220);fig.savefig(FIG/f'{name}.pdf');plt.close(fig)
for n in ['utility','privacy','attacks','influence']:chart(n)

# A standalone architecture figure for the paper.
fig,ax=plt.subplots(figsize=(8,3.8));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
def box(x,y,w,h,t,c=INDIGO):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.06',facecolor='#F8F7F3',edgecolor='#'+c,linewidth=1.5));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=9)
def arrow(x,y,xx,yy,t=''):
    ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#'+INK,'lw':1.3})
    if t:ax.text((x+xx)/2,(y+yy)/2+.12,t,ha='center',fontsize=7)
for y,label in zip([3.7,2.6,1.5,.4],['Hospital A','Hospital B','Hospital C','Hospital D']):
    box(.1,y,1.8,.65,label+'\nlocal DP-SGD',GOLD);arrow(1.95,y+.32,3.2,2.9)
box(3.2,2.5,2,.8,'Validator\nscore + reputation',VIOLET);box(6,2.5,2,.8,'Weighted masking\n+ aggregation',GREEN);arrow(5.25,2.9,5.95,2.9)
box(3.2,.45,4.8,.8,'Solidity contracts: hashes, scores, model content IDs',INDIGO);arrow(4.2,2.45,4.2,1.3,'commitments');arrow(7,2.45,7,1.3,'model hash')
box(8.5,2.5,1.4,.8,'Off-chain\nmodel bytes');arrow(8.05,2.9,8.45,2.9)
ax.text(5,4.55,'Private records stay in the simulated hospital partitions',ha='center',fontsize=10,fontweight='bold')
ax.text(5,.04,'Implementation: one-process research simulation + real local EVM execution',ha='center',fontsize=8,color='#'+MUTED)
fig.savefig(FIG/'architecture.png',dpi=220,bbox_inches='tight');fig.savefig(FIG/'architecture.pdf',bbox_inches='tight');plt.close(fig)

prs=Presentation();prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
notes=[]
def rgb(c):return RGBColor.from_string(c)
def text(sl,x,y,w,h,t,size=24,color=INK,bold=False):
    tb=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=tb.text_frame;tf.word_wrap=True
    for i,line in enumerate(t.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='DejaVu Sans';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color);p.space_after=Pt(6)
    return tb

def card(sl,x,y,w,h,t,c=INDIGO,size=22):
    s=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));s.fill.solid();s.fill.fore_color.rgb=rgb('FFFDF8');s.line.color.rgb=rgb(c);s.line.width=Pt(2)
    tf=s.text_frame;tf.word_wrap=True;tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    for i,line in enumerate(t.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.alignment=PP_ALIGN.CENTER;p.font.name='DejaVu Sans';p.font.size=Pt(size);p.font.color.rgb=rgb(c);p.font.bold=i==0
    return s

def line(sl,x,y,xx,yy,c=INDIGO):
    # Editable directional arrows with a clear arrowhead shape.
    if abs(yy-y)<.05 and xx>x:
        s=sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,Inches(x),Inches(y-.1),Inches(xx-x),Inches(.2));s.fill.solid();s.fill.fore_color.rgb=rgb(c);s.line.fill.background()
    else:
        s=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x),Inches(y),Inches(xx),Inches(yy));s.line.color.rgb=rgb(c);s.line.width=Pt(2)

def slide(title,kicker='FINAL DEFENCE',note=''):
    s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=rgb(PAPER)
    text(s,.6,.25,11,.3,kicker,11,MUTED,True);text(s,.6,.83,12.1,1.1,title,34,INK,True)
    text(s,.6,7.02,10,.25,'Sangam  ·  MAIT  ·  CSE-AIML  ·  20 November 2026',10,MUTED)
    text(s,12,7.02,.7,.25,f'{len(prs.slides):02}',10,MUTED)
    s.notes_slide.notes_text_frame.text=note;notes.append((title,note));return s

def picture(s,name,x=.9,y=2,w=11.5):s.shapes.add_picture(str(FIG/f'{name}.png'),Inches(x),Inches(y),width=Inches(w))

s=slide('Sangam','A BLOCKCHAIN-COORDINATED FEDERATED LEARNING PROTOTYPE','We built a research prototype in which four simulated hospitals train a diagnostic model together. Their records remain in their simulation partitions. Smart contracts record updates, model versions, and contribution scores. We demonstrate measured training and actual local-Ethereum execution, not a deployment in real hospitals.')
text(s,.65,2.1,10,1.5,'Many hospitals.\nOne shared model.',44,INDIGO,True)
text(s,.7,4.35,11,.7,'Patient records stay local. Contributions leave a verifiable trail.',22,MUTED)
text(s,.7,5.65,12,.7,'Divyanshh Kalra  ·  Shrey Khandal  ·  Tanish Garg\nGuide: Dr. Mohit Mittal',18)

s=slide('The team','PROJECT DETAILS','Divyanshh Kalra, Shrey Khandal, and Tanish Garg are the student authors. Dr. Mohit Mittal is the project guide. Roll numbers and institution are carried forward from the confirmed second-defence deck. The team should agree on who explains the methodology, implementation, and evaluation before the final defence.')
for x,name,roll in [(0.7,'Divyanshh Kalra','00414815623'),(4.9,'Shrey Khandal','00314815623'),(9.1,'Tanish Garg','02214815623')]:card(s,x,2.5,3.5,1.9,name+'\n'+roll,size=19)
text(s,.8,5.2,11.7,.9,'Dr. Mohit Mittal · Project Guide\nCSE-AIML-1 · Maharaja Agrasen Institute of Technology',22,INDIGO)

s=slide('The problem: learning across data silos','MOTIVATION + OBJECTIVES','A single hospital may have limited and unbalanced data. Pooling patient records creates privacy and institutional concerns. Ordinary federated learning shares model updates, but a trusted server still controls aggregation. Our objective is to combine useful learning, a recorded contribution history, and explicit privacy/robustness mechanisms in a reproducible prototype.')
for x,t in [(1,'Hospital A\nsmall dataset'),(5,'Hospital B\nskewed dataset'),(9,'Hospital C\nseparate records')]:card(s,x,2.4,3.2,1.5,t,GOLD)
text(s,1.2,4.5,11,1,'Train together without pooling records.',32,INDIGO,True)
text(s,1.2,5.7,11,.6,'Shared learning  +  update privacy  +  accountable contributions',21,MUTED)

s=slide('What existing approaches leave open','LITERATURE + RESEARCH GAP','FedAvg establishes learning through model averaging. Secure aggregation protects individual updates but does not by itself detect poisoning. Robust methods such as the median and FLTrust address malicious updates. Blockchain FL papers add coordination or incentives. Sangam studies these roles together in a small, explicit prototype; we do not claim that no previous framework combines them, or that our method is universally best.')
for y,name,what,c in [(2.05,'FedAvg','Shared learning',INDIGO),(3.02,'Secure aggregation','Update confidentiality',VIOLET),(3.99,'Median / FLTrust','Poisoning resistance',GREEN),(4.96,'Blockchain FL','Recorded coordination',GOLD)]:
    card(s,.8,y,4,.72,name,c,20);line(s,4.9,y+.36,6.1,y+.36,c);text(s,6.4,y+.05,6,.6,what,24,c)
text(s,.9,6.1,12,.5,'Sangam connects these roles and measures the trade-offs.',23,INK,True)

s=slide('The system, at a glance','ARCHITECTURE','Hospitals train locally with DP-SGD in separate simulation partitions. Validators receive the individual updates and compute scores. Reputation determines weights; pairwise masks cancel in the aggregate. Solidity stores hashes, content IDs, and scores. Off-chain storage holds the actual model bytes. In the prototype these roles execute in one Python service, and the contracts execute on a real local EVM. Validators see more than the aggregation role.')
# Editable native shapes, not a screenshot.
for i in range(4):card(s,.6,2+i*.9,2.3,.65,f'Hospital {chr(65+i)}',GOLD,18);line(s,2.95,2.32+i*.9,4.1,3.55,GOLD)
card(s,4.1,2.8,2.4,1.45,'Validators\nscore updates',VIOLET,21);line(s,6.6,3.5,7.35,3.5)
card(s,7.4,2.8,2.7,1.45,'Aggregator\ncombine updates',GREEN,21);line(s,10.2,3.5,10.6,3.5)
card(s,10.65,2.8,2.1,1.45,'Model\nstorage',INDIGO,20)
card(s,4.1,5.2,8.65,.8,'Solidity: hashes  ·  scores  ·  model content IDs',INDIGO,21);line(s,5.3,4.3,5.3,5.15);line(s,8.7,4.3,8.7,5.15)

s=slide('One round in six steps','METHODOLOGY','The aggregator first opens a round with the starting model commitment. Each hospital trains locally. Hospitals commit update hashes. Validators score the updates, and the contract updates reputations. Reputation-weighted updates are masked and summed. Finally the new model is stored off chain and its hash and content ID are committed before the round closes. Each step produces an actual transaction receipt in the integrated demonstration.')
for i,(a,b,c) in enumerate([('01','Open',INDIGO),('02','Train',GOLD),('03','Commit',INDIGO),('04','Score',VIOLET),('05','Aggregate',GREEN),('06','Close',INDIGO)]):
    x=.7+i*2.1;card(s,x,2.7,1.8,1.9,a+'\n'+b,c,24)
    if i<5:line(s,x+1.82,3.65,x+2.04,3.65,c)
text(s,1,5.4,11.5,.7,'The model changes. The evidence stays.',29,INDIGO,True)

s=slide('Privacy has two separate jobs','PRIVACY FLOW','DP-SGD clips per-example gradients and adds Gaussian noise; the accountant measures composition across training. Pairwise masking demonstrates that individual scaled updates can sum without retaining masks in the final aggregate. Validators still inspect individual DP updates to score them. The mask routine is an arithmetic simulation with reproducible seeds, not a production key-exchange and dropout-tolerant protocol. Reproducible experimental seeds must not be treated as secret production randomness.')
card(s,.9,2.5,3.4,1.5,'DP-SGD\nlimit record influence',VIOLET,23);line(s,4.4,3.25,5.1,3.25,VIOLET)
card(s,5.2,2.5,3.4,1.5,'Pairwise masks\nrecover the sum',VIOLET,23);line(s,8.7,3.25,9.3,3.25,VIOLET)
card(s,9.4,2.5,3.1,1.5,'Global model',GREEN,24)
text(s,1,5,11.5,.8,'Boundary: validators see individual DP updates.',26,INK,True)
text(s,1,6,11.5,.5,'Masking is a simulation; production key exchange remains future work.',18,MUTED)

s=slide('Bad contributions lose influence','REPUTATION + INCENTIVES','An update is scored by agreement with the median direction and by validation-loss improvement. A score below half the round median halves reputation. Other reputations move 20 percent toward the new score. Clients below one quarter of the maximum reputation are excluded; the rest are weighted by dataset size times reputation. Rewards are contribution points, not cash or tokens. In the integrated run we use the contract integer values to determine weights.')
card(s,.8,2.5,3.3,1.35,'Useful update',GREEN,23);line(s,4.2,3.15,5,3.15,GREEN);card(s,5.1,2.5,7.3,1.35,'Trust recovers gradually',GREEN,25)
card(s,.8,4.5,3.3,1.35,'Poor update',RED,23);line(s,4.2,5.15,5,5.15,RED);card(s,5.1,4.5,7.3,1.35,'Reputation halves → influence falls',RED,23)

s=slide('What we built','IMPLEMENTATION + TECHNOLOGIES','The diagnostic model is a 30–16–1 NumPy MLP with 513 parameters. Python implements the learning, scoring, DP accountant, and masking arithmetic. FastAPI joins training to the compiled Solidity contracts on a local EVM. React displays actual measurements and receipts. Supabase persists experiments and model bytes. The public deployment is a college prototype; it is not a hospital system or medical advice.')
for x,y,t,c in [(.8,2.3,'Python / NumPy\nlearning + privacy',GOLD),(5,2.3,'Solidity / EVM\ncontract execution',INDIGO),(9.2,2.3,'FastAPI\nintegration',GREEN),(.8,4.5,'React / Vite\ndashboard',INDIGO),(5,4.5,'Supabase\nrun + model storage',GREEN),(9.2,4.5,'Vercel / Render\nfree hosting',VIOLET)]:card(s,x,y,3.3,1.5,t,c,21)

s=slide('A small, reproducible benchmark','EXPERIMENTAL SETUP','Breast Cancer Wisconsin has 569 cases and 30 numeric features. The actual implementation uses 415 training, 40 validation, and 114 test records, with a stratified test split and a Dirichlet alpha 0.5 partition across four simulated hospitals. We run 30 rounds, two local epochs, batch size 16, learning rate 0.1, and ten seeds. The old draft had inconsistent split counts; these are corrected. Preprocessing is centralized in the simulation and would need a privacy-aware protocol in a real deployment.')
for x,val,label in [(.8,'569','cases'),(4.9,'4','simulated hospitals'),(9,'10','random seeds')]:
    text(s,x,2.25,3.5,1.2,val,65,INDIGO,True);text(s,x,3.55,3.5,.6,label,23)
for x,w,t in [(.8,7.6,'415 training'),(8.55,1.6,'40 val.'),(10.3,2.2,'114 test')]:card(s,x,4.7,w,.9,t,GOLD,19)
text(s,.9,6,11.5,.6,'30 rounds  ·  2 local epochs  ·  513 model parameters',22,MUTED)

s=slide('Useful learning, with a privacy cost','RESULTS · MEAN ± SD OVER TEN SEEDS','Sangam without DP reaches 97.72 percent mean accuracy; FedAvg reaches 97.63 percent and the coordinate median 97.89 percent. We do not claim Sangam is the most accurate honest-case baseline. With epsilon 4 the mean accuracy is 96.84 percent. The benefit being studied is the combination of useful learning, contribution history, and robustness. These are reproduced figures from this repository, not the old paper numbers.');picture(s,'utility',1.55,1.85,10.2)

s=slide('One attacker: FedAvg vs Sangam','ROBUSTNESS · ATTACKS EVALUATED WITHOUT DP','Hospital D attacks while the other hospitals follow ordinary non-private training. For sign flipping, FedAvg averages 35.61 percent accuracy while Sangam averages 97.19 percent. Label flipping reduces FedAvg to 87.11 percent, while Sangam stays at 97.19 percent. The median baseline is also robust. We evaluate these attacks separately from the privacy sweep; these results do not demonstrate a joint DP-plus-attack guarantee.');picture(s,'attacks',1.55,1.85,10.2)

s=slide('Poisoning earns less say in the model','ACCOUNTABILITY','The honest Hospital D has an average 23.44 percent influence under Sangam. That falls to 2.06 percent with label flipping and 2.95 percent with sign flipping. The free rider still keeps about 12.09 percent, so free-rider detection is incomplete. On-chain score history makes this weighting auditable; reputation does not prove an update is honest.');picture(s,'influence',1.55,1.85,10.2)

s=slide('Privacy is a measurable trade-off','PRIVACY–UTILITY','With delta 10 to the minus five, epsilon 1 gives 93.42 percent mean accuracy; epsilon 2 gives 95.79; epsilon 4 gives 96.84; and epsilon 8 gives 97.28. Error bars are standard deviations across ten seeds, not confidence intervals. Privacy is computed per hospital using the implemented integer-order RDP accountant, with Poisson sampling and per-example clipping. It is an experimental accounting calculation, not a certification of the deployed service.');picture(s,'privacy',1.55,1.85,10.2)

s=slide('The demo leaves evidence you can inspect','TESTING + LIVE DEMONSTRATION','Show one round in the dashboard. Open the round drawer, inspect the four update hashes, contribution scores, and eight transaction receipts. Download the global-model bytes. Paste its hash into Audit: the API checks the artifact bytes and the active contract state. Archived runs are explicitly labelled after a restart. The test suite checks unauthorized access, the complete contract lifecycle, reputation, numerical gradients, accounting equivalence, and artifact integrity.')
for i,(t,c) in enumerate([('Train\nreal model',GOLD),('Execute\n8 transactions',INDIGO),('Download\nmodel bytes',GREEN),('Verify\nmatching hash',VIOLET)]):
    x=.8+i*3.2;card(s,x,2.55,2.9,1.7,t,c,23)
    if i<3:line(s,x+2.92,3.4,x+3.17,3.4,c)
text(s,1,5.2,11.5,.8,'Local EVM receipts are labelled as local.',28,INDIGO,True)
text(s,1,6.1,11.5,.5,'Measured gas and timing are reported separately from the old draft.',18,MUTED)

s=slide('What this prototype does — and what comes next','CONCLUSION + FUTURE SCOPE','The contribution is a reproducible integration of reputation-weighted learning, privacy accounting, and a real contract audit trail, evaluated on one small public dataset. Limitations include four simulated hospitals, centralized simulation preprocessing, validator visibility, incomplete free-rider detection, and no binding proof between a masked input and its commitment. Next steps are independent hospital processes, secret pairwise key agreement, funded Amoy deployment, medical images, and stronger adaptive-attack evaluation. Publication is a separate review process and is not claimed as completed.')
card(s,.8,2.35,5.6,2.1,'Built\nshared learning + measured results\nreal contract audit trail',GREEN,22)
card(s,6.9,2.35,5.6,2.1,'Next\nindependent hospital clients\nproduction privacy + testnet',INDIGO,22)
text(s,1,5.35,11.5,.9,'Many rivers. One model. A record of every contribution.',29,GOLD,True)

s=slide('References','SELECTED PRIMARY SOURCES','The manuscript contains the full references. The presentation cites the original FedAvg, secure aggregation, DP-SGD, RDP accounting, robust aggregation, and FLTrust work. We distinguish features described in those papers from the simplified implementation in Sangam.')
refs_short=['McMahan et al. · FedAvg · AISTATS 2017','Bonawitz et al. · Secure Aggregation · CCS 2017','Abadi et al. · DP-SGD · CCS 2016','Mironov · Rényi Differential Privacy · CSF 2017','Yin et al. · Byzantine-robust Distributed Learning · ICML 2018','Cao et al. · FLTrust · NDSS 2021']
for i,t in enumerate(refs_short):text(s,.9,2+i*.65,11.8,.5,t,20,INDIGO)
prs.save(OUT/'Sangam_Final_Defence.pptx')
(OUT/'SPEAKER_NOTES.md').write_text('# Speaker notes\n\n'+'\n\n'.join(f'## {i+1}. {t}\n\n{n}' for i,(t,n) in enumerate(notes)))

# Canonical manuscript content: same source feeds PDF, editable Word and Markdown.
TITLE='Sangam: A Blockchain-Coordinated Prototype for Auditable Federated Learning in Healthcare'
AUTHORS='Divyanshh Kalra, Shrey Khandal, Tanish Garg, and Dr. Mohit Mittal'
AFFILIATION='Department of CSE-AIML, Maharaja Agrasen Institute of Technology, Rohini, New Delhi, India'
refs=[
'[1] B. McMahan et al., “Communication-Efficient Learning of Deep Networks from Decentralized Data,” AISTATS, PMLR 54, pp. 1273–1282, 2017. https://proceedings.mlr.press/v54/mcmahan17a.html',
'[2] K. Bonawitz et al., “Practical Secure Aggregation for Privacy-Preserving Machine Learning,” ACM CCS, 2017. doi:10.1145/3133956.3133982.',
'[3] M. Abadi et al., “Deep Learning with Differential Privacy,” ACM CCS, 2016. doi:10.1145/2976749.2978318.',
'[4] I. Mironov, “Rényi Differential Privacy,” IEEE CSF, 2017. doi:10.1109/CSF.2017.11.',
'[5] I. Mironov, K. Talwar and L. Zhang, “Rényi Differential Privacy of the Sampled Gaussian Mechanism,” 2019. arXiv:1908.10530.',
'[6] D. Yin et al., “Byzantine-Robust Distributed Learning: Towards Optimal Statistical Rates,” ICML, PMLR 80, pp. 5650–5659, 2018. https://proceedings.mlr.press/v80/yin18a.html',
'[7] X. Cao et al., “FLTrust: Byzantine-Robust Federated Learning via Trust Bootstrapping,” NDSS, 2021. doi:10.14722/ndss.2021.24434.',
'[8] W. Wolberg, O. Mangasarian, N. Street and W. Street, “Breast Cancer Wisconsin (Diagnostic),” UCI Machine Learning Repository, 1995. doi:10.24432/C5DW2B.',
'[9] H. Kim, J. Park, M. Bennis and S.-L. Kim, “Blockchained On-Device Federated Learning,” IEEE Communications Letters, vol. 24, no. 6, pp. 1279–1283, 2020. doi:10.1109/LCOMM.2019.2921755.',
'[10] J. Weng et al., “DeepChain: Auditable and Privacy-Preserving Deep Learning with Blockchain-Based Incentive,” IEEE Transactions on Dependable and Secure Computing, vol. 18, no. 5, pp. 2438–2455, 2021. doi:10.1109/TDSC.2019.2952332.',
'[11] Sangam source code and reproducibility materials. https://github.com/TechnicallyKiller/sangam/tree/submission/final-defence (accessed 16 November 2026).'
]
mu=lambda k,m='acc':f"{R[k][m][0]:.2f} ± {R[k][m][1]:.2f}"
gas=[sum(t['gas'] for t in r['txs']) for r in LIVE['rounds']]
items=[]
def h(t):items.append(('h',t))
def p(t):items.append(('p',t))
def f(name,caption):items.append(('f',(name,caption)))
def table(headers,rows,caption):items.append(('t',(headers,rows,caption)))
h('Abstract')
p(f'Hospitals can collaborate on diagnostic models without pooling patient records, but ordinary federated averaging relies on an aggregation service and provides little persistent evidence about contributions. Sangam is a reproducible prototype combining contribution scoring, asymmetric reputation, experimental privacy accounting, and Solidity-based coordination. Four simulated hospitals train a 513-parameter model on the Breast Cancer Wisconsin benchmark. Across ten seeds, non-private Sangam achieves {mu("sangam")}% test accuracy, compared with {mu("fedavg")}% for FedAvg. Under a sign-flipping client, these figures are {mu("sign_flip/sangam")}% and {mu("sign_flip/fedavg")}%, respectively. A separate privacy sweep reaches {mu("sangam_eps4")}% at epsilon 4 and delta 10^-5. The integrated service executes actual local-Ethereum transactions and verifies stored model bytes against their on-chain commitment. The implementation remains a one-process research simulation: masking is arithmetic rather than a production cryptographic protocol, validators inspect individual updates, and testnet deployment is not claimed. The contribution is transparent integration and reproducible evaluation, rather than a new privacy proof or clinical validation.')
p('Keywords: federated learning; blockchain coordination; reputation; differential privacy; secure aggregation simulation; healthcare benchmark.')
h('1. Introduction')
p('Medical datasets are often distributed across institutions. Federated learning exchanges model updates instead of pooling the underlying records [1], but a standard server still determines how contributions are combined. An audit log can make model provenance and contribution history visible without recording patient records on chain. Update confidentiality and robustness remain separate requirements: hashes do not hide an update already disclosed to a validator, and an immutable log does not establish that an update is correct.')
p('Sangam connects these concerns in a small benchmark prototype. Hospitals contribute updates; a validation role scores them; persistent reputations determine aggregation weights; a masking simulation demonstrates sum recovery; and two contracts enforce a round lifecycle and record contribution scores. A dashboard exposes measured results and actual transaction receipts. We ask three practical questions: how much utility is retained relative to ordinary baselines, how the weighting reacts to simple malicious clients, and what privacy-accounting and chain overhead accompany the design.')
p('The contributions are (i) an executable integration with content-addressed model storage and contract-level provenance, (ii) a ten-seed comparison including privacy and attack experiments, and (iii) explicit correspondence between the published evidence, implementation, and limitations. We do not claim novelty for FedAvg, DP-SGD, additive masking, or reputation updates individually, nor superiority over all robust aggregation methods.')
h('2. Related work and research positioning')
p('FedAvg averages locally trained parameters according to client data sizes [1]. Secure aggregation protocols can reveal only a combined update, but require cryptographic setup and mechanisms for failed or malicious clients [2]. DP-SGD clips per-example gradients and adds calibrated Gaussian noise [3]; Rényi differential privacy provides a composition framework [4,5]. These mechanisms address different information flows and cannot be substituted for each other.')
p('The coordinate-wise median is a standard robust baseline [6]. FLTrust uses a trusted root dataset to assess client updates [7]. Blockchain approaches such as BlockFL and DeepChain explore coordination, auditability, or incentives [9,10]. Sangam is positioned as an integration study: a small, inspectable implementation showing how these roles interact. Reputation points are accounting units, not a financial reward, and recording a score on chain does not prove the scoring service behaved honestly.')
h('3. System and threat model')
p('The design has four hospital roles, a validator, an aggregator, two Ethereum-compatible contracts, and off-chain model storage. The consortium owner admits participants. The validator sees individual updates and a held-out validation set; the aggregator combines weighted updates. In this implementation all learning roles share one Python process and data are partitioned in memory. This reproduces the algorithm but does not demonstrate institutional isolation or a distributed network protocol.')
p('The experimental attacker is hospital D. We separately test flipped labels, an update multiplied by -5, and a free rider that supplies norm-scaled Gaussian noise instead of training. We assume the coordinator and validator follow their prescribed computations. Sybil admission, validator collusion, adaptive attacks, verified dataset sizes, and patient-level reconstruction attacks are outside the evaluation. Fewer than half the clients are malicious in the tested setting; that is an experimental condition, not a general robustness theorem.')
f('architecture','Figure 1. Logical data flow. Training roles are simulated in one service; the compiled contracts execute on a local EVM. Validators inspect individual updates before weighted aggregation.')
h('4. Methodology')
p('Let w be the global parameter vector and d_k a hospital update. Each client runs two local epochs. In a private experiment, each record is sampled independently with q_k=min(1,b/n_k), its gradient is clipped to norm C=1, and Gaussian noise with standard deviation sigma_k C is added to the gradient sum before division by the expected batch size. Sigma_k is calibrated for all 30 rounds using integer RDP orders 2 through 128 and delta=10^-5 [3–5]. The same accountant evaluates the accumulated honest-client budget. Seeds are fixed for reproducibility on a public benchmark, not used as secret production randomness.')
p('Updates are bounded to the median client-update norm. The validator computes cosine agreement with the coordinate-wise median and the relative validation-loss improvement gamma_k. The contribution score is s_k = max(0,cos_k)/max_j max(0,cos_j) times min(1,2 sigmoid(20 gamma_k)). This is a heuristic consistency-and-utility score, not a proof of honesty. A participant may occasionally align by chance, which is particularly relevant for free riding.')
p('Reputation starts at 0.5. If a score is below half the round median, reputation is halved; otherwise r_k becomes 0.8 r_k + 0.2 s_k. Clients below one quarter of the maximum reputation receive zero weight. Remaining weights are proportional to n_k r_k and normalized to sum to one. The integrated path uses the contract’s integer scores and reputations, while research simulations use floating point. These two implementations can produce slightly different trajectories; their evidence is reported separately.')
p('For masking, updates are multiplied by their weights, quantized with 20 fractional bits, and represented modulo 2^32. Equal and opposite pseudorandom pairwise masks cancel when summed. The implementation demonstrates cancellation and quantization accuracy. It does not implement authenticated pairwise key exchange, dropout recovery, or a proof binding a masked input to its committed unmasked update. Because the validator receives individual updates, it retains more visibility than the logical aggregation role.')
h('5. Implementation and reproducibility')
p('SangamCoordinator restricts participant admission and round management, rejects duplicate and late submissions, records starting and global-model hashes/content IDs, and enforces Open → Aggregated → Closed transitions. ReputationRegistry accepts one score batch per participant and round, computes the asymmetric update in basis points, and accumulates reward points. Solidity 0.8.24 is compiled with 200 optimizer runs. The integrated service uses Web3 and an in-process Ethereum test chain; it does not claim Polygon Amoy transactions.')
p('FastAPI exposes runs, rounds, participants, model downloads, and hash verification. Read endpoints are public; experiment creation requires a private operator token. The service submits transactions for the simulated hospital accounts. React displays API values rather than generated curves. Model artifacts are little-endian float64 bytes, keyed by a SHA-256 raw CIDv1; their Keccak-256 commitments are checked against the contracts. SQLite supports a local run and PostgreSQL/Supabase supports hosted persistence. These content-addressed objects are not described as publicly pinned to IPFS.')
p('The public UCI diagnostic dataset [8] contains 569 cases and 30 features. A stratified 20% test holdout gives 114 cases. The implemented 7% validation allocation gives 40 validation cases and leaves 415 training cases. Training features are standardized using pooled training statistics in the simulation; a real deployment would need a public or privacy-aware normalization protocol. The training cases are distributed across four hospitals using a Dirichlet label partition with alpha=0.5 and a minimum 8% share of each class per client. Thus the partition is non-IID but deliberately avoids nearly empty clients.')
p('The model is a 30–16–1 ReLU/sigmoid MLP with 513 parameters. We run 30 rounds, two local epochs, batch size 16, and learning rate 0.1. Baselines are centralized training, the mean of four local-only models, size-weighted FedAvg, and coordinate-wise median aggregation. The ten seeds are 0–9. Tables report mean and population standard deviation (ddof=0). F1 treats benign cases, dataset label 1, as positive. These conventions are explicit because benign-positive F1 is not malignant-case sensitivity.')
p('Reproduction commands and per-seed outputs are included with the repository. Privacy sweeps and robustness experiments are separate: the attack comparison is non-private and cannot establish joint DP-plus-poisoning performance. The centralized and federated procedures use the specified local-epoch schedules, which do not equalize all optimization steps or computational budgets. Results are exploratory benchmark evidence, not clinical effectiveness estimates.')
h('6. Results')
table(['Method','Accuracy %','ROC-AUC %','F1 %'],[[label,mu(k),mu(k,'auc'),mu(k,'f1')] for k,label in [('centralised','Centralised'),('local_only','Local only'),('fedavg','FedAvg'),('median','Median'),('sangam','Sangam'),('sangam_eps4','Sangam, DP 4')]],'Table 1. Honest-case utility, mean ± SD over ten seeds.')
p('Non-private Sangam retains high accuracy but does not dominate the median baseline. Its mean is 0.09 percentage points above FedAvg and 1.51 points above local-only training. The small benchmark and overlapping variability do not support a general superiority claim. The integrated single-seed run uses contract quantization and is not substituted for the multi-seed table.')
f('privacy','Figure 2. Privacy–utility sweep; error bars are standard deviations across seeds. Smaller epsilon uses stronger noise.')
table(['Attack','FedAvg acc.','Median acc.','Sangam acc.'],[[a.replace('_',' ').title(),mu(a+'/fedavg'),mu(a+'/median'),mu(a+'/sangam')] for a in ['label_flip','sign_flip','free_rider']],'Table 2. Non-private attack comparison, mean ± SD (%).')
p('Sangam and the median remain near 97% for the tested label- and sign-flipping attacks. FedAvg is especially unstable under sign flipping, with a large across-seed deviation. This is consistent with sensitivity to an adversarial client’s data share. Sangam’s mean attacker influence is 2.06% for label flipping and 2.95% for sign flipping, compared with 23.44% for the honest control. Free-rider influence remains 12.09%; suppression is partial, not complete.')
p(f'The integrated honest run completes {len(LIVE["rounds"])} rounds and {sum(len(r["txs"]) for r in LIVE["rounds"])} actual round transactions. The mean round gas is {statistics.mean(gas):,.0f}, with first-round gas {gas[0]:,} and a range of {min(gas):,}–{max(gas):,}. These receipts include real content IDs and contract storage updates on the local EVM; they are not the old draft’s 668,449-gas estimate. Timing includes training, contract execution, accounting, and persistence, so it is not a network latency benchmark. Model downloads are verified byte-for-byte against Keccak commitments.')
h('7. Limitations and future work')
p('The experiment uses one small tabular dataset and four simulated clients. A curated validation set is trusted, and global normalization is centralized in the simulator. Neither a hospital-grade deployment nor a clinical use claim is justified. Private training uses a custom accountant and reproducible statistical experiments; production use would require audited accounting, secret randomness, a preprocessing privacy analysis, and secure client isolation.')
p('Scoring reveals individual DP-protected updates to validators. The arithmetic masking simulation alone is not a production confidentiality guarantee. The protocol does not prove that a masked input matches its on-chain hash, that a model was correctly aggregated, or that claimed client dataset sizes are truthful. Reputation is heuristic and only partly detects free riding. Medical-imaging benchmarks, more clients, adaptive attacks, independent hospital processes, authenticated key agreement, verifiable aggregation, and public-testnet deployment are future work.')
h('8. Conclusion')
p('Sangam demonstrates a coherent path from federated training to recorded contribution history and model provenance. Reproduced experiments show useful honest-case utility, a privacy–utility trade-off, and resistance to simple poisoning attacks comparable to a robust median baseline. The local-EVM integration provides inspectable receipts and verifiable model artifacts. Its value for this submission is a working, reproducible prototype with bounded claims and explicit limitations.')
h('Data and code availability')
p('The data are public through UCI and scikit-learn [8]. Source code, configuration, per-seed experiment outputs, local-EVM receipts, and figure-generation sources are available in the Sangam repository [11]. No private patient records were collected. The interactive dashboard and evaluation outputs represent different runs and are labelled accordingly.')
h('Declarations')
p('This work used an existing public, de-identified benchmark and did not recruit human participants. No external project funding is claimed. Generative AI assisted implementation, manuscript drafting, document layout, and verification; the authors remain responsible for checking the code, references, measurements, and final text.')
h('References')
for ref in refs:p(ref)

# Markdown, suitable for reviewing exactly what changed.
md=[f'# {TITLE}',AUTHORS,AFFILIATION]
for typ,val in items:
    if typ=='h':md.append('## '+val)
    elif typ=='p':md.append(val)
    elif typ=='f':md.append(f'![{val[1]}](figures/{val[0]}.png)')
    else:
        head,rows,cap=val;md.extend([cap,'| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(row)+' |' for row in rows])
(OUT/'Sangam_Final_Paper.md').write_text('\n\n'.join(md))

# Editable Word source.
doc=Document();sec=doc.sections[0];sec.top_margin=DI(.7);sec.bottom_margin=DI(.7);sec.left_margin=DI(.75);sec.right_margin=DI(.75)
doc.styles['Normal'].font.name='Times New Roman';doc.styles['Normal'].font.size=DP(11)
doc.add_heading(TITLE,0);doc.add_paragraph(AUTHORS);doc.add_paragraph(AFFILIATION)
for typ,val in items:
    if typ=='h':doc.add_heading(val,1)
    elif typ=='p':doc.add_paragraph(val)
    elif typ=='f':doc.add_picture(str(FIG/f'{val[0]}.png'),width=DI(6.6));doc.add_paragraph(val[1],style='Caption')
    else:
        heads,rows,cap=val;doc.add_paragraph(cap,style='Caption');t=doc.add_table(rows=1,cols=len(heads));t.style='Light Shading Accent 1'
        for cell,v in zip(t.rows[0].cells,heads):cell.text=v
        for row in rows:
            for cell,v in zip(t.add_row().cells,row):cell.text=v
footer=sec.footer.paragraphs[0];footer.text='Sangam · Author review copy · November 2026'
doc.save(OUT/'Sangam_Final_Paper.docx')

# Two-column academic PDF; all content comes from the same manuscript source.
W,H=A4; margin=35; gap=16;cw=(W-2*margin-gap)/2
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyAcademic',fontName='Times-Roman',fontSize=9,leading=11.2,alignment=TA_JUSTIFY,spaceAfter=6));styles.add(ParagraphStyle(name='HeadAcademic',fontName='Helvetica-Bold',fontSize=10,leading=12,spaceBefore=9,spaceAfter=5));styles.add(ParagraphStyle(name='CapAcademic',fontName='Times-Italic',fontSize=8,leading=9,spaceAfter=7));styles.add(ParagraphStyle(name='CellAcademic',fontName='Helvetica',fontSize=6.4,leading=8))
def esc(s):return html.escape(s).replace('–','-').replace('→','to').replace('Δ','delta').replace('ε','epsilon')
def page(c,d,first=False):
    c.setFillColor(colors.HexColor('#'+INK));c.setFont('Helvetica',7);c.drawString(margin,20,'Sangam | Reproducible research prototype | November 2026');c.drawRightString(W-margin,20,str(d.page))
    if first:
        c.setFont('Helvetica-Bold',14);c.drawCentredString(W/2,H-48,'Sangam: A Blockchain-Coordinated Prototype for')
        c.drawCentredString(W/2,H-67,'Auditable Federated Learning in Healthcare')
        c.setFont('Helvetica',8);c.drawCentredString(W/2,H-89,AUTHORS);c.setFont('Helvetica',7);c.drawCentredString(W/2,H-104,AFFILIATION)
    else:
        c.setFont('Helvetica',7);c.drawString(margin,H-23,'Sangam: Auditable Federated Learning')
frames=lambda top:[Frame(margin,34,cw,top-34,id='left'),Frame(margin+cw+gap,34,cw,top-34,id='right')]
pdf=BaseDocTemplate(str(OUT/'Sangam_Final_Paper.pdf'),pagesize=A4,leftMargin=margin,rightMargin=margin,title=TITLE,author=AUTHORS)
pdf.addPageTemplates([PageTemplate(id='first',frames=frames(H-120),onPage=lambda c,d:page(c,d,True)),PageTemplate(id='normal',frames=frames(H-35),onPage=page)])
story=[NextPageTemplate('normal')]
for typ,val in items:
    if typ=='h':story.append(Paragraph(esc(val),styles['HeadAcademic']))
    elif typ=='p':story.append(Paragraph(esc(val),styles['BodyAcademic']))
    elif typ=='f':
        from PIL import Image as PI
        im=PI.open(FIG/f'{val[0]}.png');iw,ih=im.size
        story.append(KeepTogether([Image(str(FIG/f'{val[0]}.png'),width=cw-12,height=(cw-12)*ih/iw),Paragraph(esc(val[1]),styles['CapAcademic'])]))
    else:
        heads,rows,cap=val;data=[[Paragraph(esc(v),styles['CellAcademic']) for v in row] for row in [heads]+rows]
        widths=[cw*.27]+[(cw*.73)/(len(heads)-1)]*(len(heads)-1)
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAE7DE')),('LINEBELOW',(0,0),(-1,0),.5,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(KeepTogether([Paragraph(esc(cap),styles['CapAcademic']),t,Spacer(1,7)]))
pdf.build(story)
print('Built 17-slide editable deck, speaker notes, final paper (PDF/DOCX/Markdown), and five scientific figures')

# Optional journal-styled source using the publisher's downloaded Word template.
template=ROOT/'tools/templates/Informatica2026.docx'
if template.exists():
    from docx.enum.section import WD_SECTION_START
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    journal=Document(template)
    for child in list(journal._element.body):
        if child.tag != qn('w:sectPr'): journal._element.body.remove(child)
    for sec in journal.sections:
        for area in (sec.header,sec.footer):
            for child in list(area._element): area._element.remove(child)
        cols=sec._sectPr.find(qn('w:cols'))
        if cols is None: cols=OxmlElement('w:cols');sec._sectPr.append(cols)
        cols.set(qn('w:num'),'1')
    def js(preferred): return preferred if preferred in journal.styles else 'Normal'
    journal.add_paragraph(TITLE,style=js('I_Title'))
    journal.add_paragraph(AUTHORS,style=js('I_Authors'))
    journal.add_paragraph(AFFILIATION,style=js('I_Authors'))
    journal.add_paragraph('Manuscript for editorial review; not an accepted or published article.',style=js('I_Received'))
    abstract=items[1][1]
    journal.add_paragraph(abstract,style=js('I_Abstract'))
    journal.add_paragraph(items[2][1],style=js('I_Keywords'))
    sec=journal.add_section(WD_SECTION_START.CONTINUOUS)
    cols=sec._sectPr.find(qn('w:cols'))
    if cols is None:cols=OxmlElement('w:cols');sec._sectPr.append(cols)
    cols.set(qn('w:num'),'2');cols.set(qn('w:space'),'360')
    for typ,val in items[3:]:
        if typ=='h':journal.add_paragraph(re.sub(r'^\d+\.\s*', '', val),style=js('I_References' if val == 'References' else 'I_SectionTitle'))
        elif typ=='p':journal.add_paragraph(val,style=js('I_Bibliography' if val.startswith('[') else 'I_Text'))
        elif typ=='f':
            journal.add_picture(str(FIG/f'{val[0]}.png'),width=DI(3.05))
            journal.add_paragraph(val[1],style=js('I_FigureCaption'))
        else:
            heads,rows,caption=val;journal.add_paragraph(caption,style=js('I_TableCaption'))
            t=journal.add_table(rows=1,cols=len(heads));t.autofit=False
            for cell,v in zip(t.rows[0].cells,heads):cell.text=v
            for row in rows:
                for cell,v in zip(t.add_row().cells,row):cell.text=v
            for row in t.rows:
                for cell in row.cells:
                    cell.width=DI(3.05/len(heads))
                    for par in cell.paragraphs:
                        for run in par.runs:run.font.name='Times New Roman';run.font.size=DP(7)
    journal.core_properties.title=TITLE;journal.core_properties.author=AUTHORS
    journal.save(OUT/'Sangam_Informatica_Manuscript.docx')
    print('Built journal-styled source from the official Informatica Word template')

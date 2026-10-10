// Editable local presentation. Run using the bundled artifact Node runtime.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtime = process.env.RUNTIME_NODE_MODULES;
const skill = process.env.SKILL_DIR;
if (!runtime || !skill || !process.env.RUNTIME_PYTHON) throw new Error('Supply authoritative bundled runtime and skill paths.');
const { Presentation, PresentationFile, FileBlob } = await import(pathToFileURL(path.join(runtime, '@oai/artifact-tool/dist/artifact_tool.mjs')));
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')));
const family = resolvePresentationFont();
const build = path.join(root, 'qa/experiments/submission/slides');
const output = path.join(root, 'docs/submission');
await fs.mkdir(build, { recursive: true });
await fs.mkdir(output, { recursive: true });
const evaluation = JSON.parse(await fs.readFile(path.join(root, 'results/model-evaluation.json'), 'utf8'));
const benchmark = JSON.parse(await fs.readFile(path.join(root, 'results/algorithm-verification.json'), 'utf8'));
const ppt = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C = { green: '#236b4d', ink: '#20382e', muted: '#607268', pale: '#edf5ef', purple: '#8a79a1', light: '#75a88a' };
const source = 'Sources: results/model-evaluation.json, results/algorithm-verification.json, models/ecosplice-v1/manifest.json. Frozen development artifacts, not live timings.';
function text(slide, value, x, y, w, h, size=27, color=C.ink, bold=false) {
  const shape = slide.shapes.add({ geometry: 'textbox', position: { left:x,top:y,width:w,height:h }, fill:'none', line:{fill:'none',width:0} });
  shape.text = value;
  shape.text.style = { typeface:family, fontSize:size, color, bold, autoFit:'none' };
  return shape;
}
function slide(title, note) {
  const s = ppt.slides.add(); s.background.fill = '#ffffff';
  text(s,title,64,40,1152,80,44,C.ink,true);
  s.speakerNotes.textFrame.setText(note);
  return s;
}
function foot(s, value) { text(s,value,64,636,1152,60,21,C.muted); }
function table(s, values, y, widths, height=280) {
  const t = s.tables.add({rows:values.length,columns:values[0].length,left:64,top:y,width:1152,height,columnWidths:widths,values});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({
    textStyle:{typeface:family,fontSize:24,color:C.ink}, margins:{left:14,right:14,top:12,bottom:12}, anchor:'center',
  });
  t.borders.assign({fill:'#d9e3dc',width:1,style:'solid'});
  t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:C.pale,textStyle:{bold:true}});
  return t;
}
function box(s, title, detail, x,y,w,h=105) {
  const a=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:C.pale,line:{fill:C.green,width:1.5}});
  text(s,title,x+18,y+16,w-36,37,29,C.green,true);
  text(s,detail,x+18,y+58,w-36,h-64,23);
  return a;
}
function arrow(s,x,y,w,h,down=false) {
  s.shapes.add({geometry:down?'downArrow':'rightArrow',position:{left:x,top:y,width:w,height:h},fill:C.green,line:{fill:'none',width:0}});
}
function chart(s,categories,series,max,unit,{y=142,h=452,labels=false}={}) {
  const ch=s.charts.add('bar',{position:{left:64,top:y,width:1152,height:h},categories,series,
    barOptions:{direction:'column',grouping:'clustered',gapWidth:110},hasLegend:true,
    legend:{position:'bottom',overlay:false,textStyle:{typeface:family,fontSize:23,fill:C.ink}},
    xAxis:{textStyle:{typeface:family,fontSize:22,fill:C.ink},majorGridlines:null},
    yAxis:{min:0,max,numberFormatCode:max===1?'0.0':'0',title:{text:unit,textStyle:{typeface:family,fontSize:21,fill:C.ink}},textStyle:{typeface:family,fontSize:20,fill:C.ink},majorGridlines:{fill:'#e3e9e5',width:1}},
    dataLabels:{showValue:labels,position:'outEnd',textStyle:{typeface:family,fontSize:22,fill:C.ink}},
    chartFill:'#ffffff',plotAreaFill:'#ffffff',chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
  });
  applyPresentationChartFont(ch,{fontFamily:family}); return ch;
}

// 1 Cover
let s=ppt.slides.add(); s.background.fill=C.pale;
text(s,'EcoSplice',80,165,1120,104,78,C.green,true);
text(s,'Local DNA splice boundary analysis',80,285,1070,130,48,C.ink,true);
text(s,'Real predictions and measured algorithm comparisons',80,455,1080,65,29);
text(s,'Final application demonstration     9 October 2026',80,565,1080,50,23,C.muted);
s.speakerNotes.textFrame.setText('EcoSplice predicts possible canonical boundaries from DNA context. It runs locally with React, FastAPI, NumPy and SQLite. This presentation describes the implemented system and its frozen results. Use docs/submission/DEMO_SCRIPT.md for the four-minute live flow.');

// 2 Scope and coordinates
s=slide('Input and prediction scope','Source: docs/DATASET_AND_COORDINATES.md and backend/ecosplice/sequence.py. Canonical GT donor and AG acceptor candidates only. Input is supplied in the direction to analyse. Minus-strand bundled demos are already oriented. Donor boundary is before GT and acceptor boundary after AG. Scores require 102 ACGT bases.');
text(s,'Paste DNA or upload one FASTA record',64,145,1152,50,33,C.green,true);
text(s,'A/C/G/T/N, at least 20 called bases, up to 100,000 bases',64,209,1152,64,28);
box(s,'50 bases','Complete A/C/G/T context',64,315,360,120);
box(s,'GT or AG','Two-base canonical motif',460,315,360,120);
box(s,'50 bases','Complete A/C/G/T context',856,315,360,120);
text(s,'One-based motif starts in the supplied orientation',64,485,1152,52,31,C.green,true);
text(s,'Incomplete or N-containing contexts remain visible with no score.',64,552,1152,62,26);
foot(s,'Outputs identify possible boundaries. Complete intron pairing and sequence removal remain outside this version.');

// 3 Architecture
s=slide('Local application architecture','Sources: backend/ecosplice/local_app.py, api.py, algorithms.py, storage.py, reports.py and frontend/src/useWorkspace.js. One loopback process serves built React and the API. Scientific snapshots persist locally. Training and source downloads are development-only utilities.');
box(s,'React dashboard','DNA input and results',64,145,440);
box(s,'FastAPI service','Validation and run APIs',760,145,456);
arrow(s,548,178,166,35);
box(s,'SQLite history','Saved scientific snapshots',64,405,440);
box(s,'Analysis engine','Saved models and three methods',760,290,456);
arrow(s,963,254,48,31,true);
box(s,'Shared report renderer','CSV, JSON and printable HTML',760,460,456);
// Route measured results into history; exports read that stored snapshot.
s.shapes.add({geometry:'line',position:{left:676,top:343,width:84,height:0},line:{fill:C.green,width:3}});
s.shapes.add({geometry:'line',position:{left:676,top:343,width:0,height:62},line:{fill:C.green,width:3}});
s.shapes.add({geometry:'leftArrow',position:{left:520,top:401,width:173,height:32},fill:C.green,line:{fill:'none',width:0}});
arrow(s,548,437,166,35);
text(s,'Predictions and measurements save to SQLite.',64,291,470,90,27);
foot(s,'One localhost address serves the interface and API. Normal inference uses no cloud service or internet.');

// 4 Data
s=slide('Real data and isolated partitions','Sources: data/processed/manifest.json and split_membership.json; https://www.gencodegenes.org/human/release_49.html ; https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/ . GENCODE open-access source terms and scientific attribution remain with samples. Seed 20261006. Full groups stay in one partition.');
text(s,'GENCODE v49 with GRCh38 primary chromosome 22 DNA',64,140,1152,60,31,C.green,true);
table(s,[['Partition','Donor','Acceptor','Non-site','Total'],['Train','3,654','3,811','85,766','93,231'],['Validation','858','821','18,474','20,153'],['Test','900','918','19,401','21,219']],225,[245,210,210,245,242],270);
text(s,'400 genes form 304 groups and 134,603 unique contexts.',64,525,1152,52,27);
foot(s,'Overlap groups stay in one split. Global deduplication includes reverse complements. Unannotated negatives may include unknown activity.');

// 5 Models
s=slide('Saved prediction models',source+' Detailed logistic regression uses base and adjacent-pair position features. Preliminary uses bases only. Training fits train, validation selects thresholds and routes. Softmax reflects sampled balance. No probability calibration transform was fit.');
table(s,[['Scorer','Context','Features','Donor','Acceptor'],['Preliminary','22 bases','Single bases','0.36','0.31'],['Detailed','102 bases','Bases and pairs','0.41','0.44']],150,[245,185,342,190,190],230);
text(s,'Thresholds and adaptive settings freeze on validation.',64,432,1152,54,31,C.green,true);
text(s,'Opening EcoSplice loads saved numeric coefficients.\nTraining is a separate development step.',64,506,1152,96,28);
foot(s,'Scores are model scores under sampled class balance. A score is not an established biological probability.');

// 6 Methods
s=slide('Three implemented algorithms',source+' Sources: backend/ecosplice/algorithms.py and docs/MODELS_AND_ALGORITHMS.md. e is all eligible contexts, q eligible canonical contexts and m uncertain canonical contexts. Baseline really evaluates ordinary positions. All use bounded batches.');
table(s,[['Method','Processing','Detailed calls','Preliminary calls'],['Exhaustive','Every eligible position','e','0'],['Filtered','Eligible GT/AG only','q','0'],['Adaptive','Cheap first, escalate uncertain','m','q']],155,[215,505,210,222],305);
text(s,'All three remain O(n) for a fixed context and model.',64,504,1152,55,32,C.green,true);
text(s,'Filtering reduces expensive evaluations while preserving canonical results.',64,573,1152,70,26);

// 7 Routing
s=slide('Adaptive routing performs less detailed work',source+' Frozen donor decisive range <=0.18 or >=0.52. Acceptor <=0.0775 or >=0.655. Use the applicable final scorer threshold, not the route threshold, for the final decision. Detailed scorer is called only for uncertain contexts.');
box(s,'Eligible canonical candidate','Complete 102-base context',410,137,460,102);
arrow(s,614,243,51,32,true);
box(s,'Preliminary scorer','Reads the central 22 bases',410,286,460,102);
text(s,'Decisive score',156,403,390,45,26,C.green,true);
text(s,'Uncertain score',786,403,390,45,26,C.green,true);
box(s,'Fast final result','Uses preliminary score and threshold',64,466,516,110);
box(s,'Detailed final result','Evaluates the 102-base context',700,466,516,110);
foot(s,'The saved result records the actual final scorer and route. Adaptive predictions can differ from the detailed reference.');

// 8 Quality
s=slide('Held-out prediction quality',source+' Canonical donor domain 7497, support900; acceptor domain7523, support918. Detailed confusion donor TP712 FP171 FN188 TN6426; acceptor TP637 FP221 FN281 TN6384. Rounded display values from full-precision JSON. Adaptive avoids12132/15020 detailed evaluations, 80.77 percent. Donor F1 drop0.0129 exceeds the validation tolerance0.005. No test tuning.');
chart(s,['Donor','Acceptor'],['detailed','adaptive'].map((m,i)=>({name:m==='detailed'?'Detailed':'Adaptive',values:['donor','acceptor'].map(k=>Number(evaluation.test[m][k].canonical_candidates.f1.toFixed(3))),valuesFormatCode:'0.000',dataLabelOverrides:['donor','acceptor'].map((k,idx)=>({idx,text:evaluation.test[m][k].canonical_candidates.f1.toFixed(3),position:'outEnd',showValue:false,textStyle:{typeface:family,fontSize:22,fill:C.ink}})),fill:[C.green,C.purple][i]})),1,'F1',{labels:true,h:430});
text(s,'80.77% fewer detailed test evaluations',64,579,1152,50,31,C.green,true);
foot(s,'Adaptive donor F1 falls from 0.7987 to 0.7858. Acceptor F1 rises from 0.7173 to 0.7238. Sampled chr22 results.');

// 9 Runtime
s=slide('Measured runtime on real held-out regions',source+' Five repeats, shuffled method order, one excluded warm-up per method, batch512. Windows11 AMD64 Family25 Model68 Stepping1,16logicalCPUs Python3.12.10 NumPy2.2.6. Runtime excludes startup/HTTP/UI/serialization/SQLite writes. Raw totals and IQR are in source artifact.');
chart(s,['TBC1D22A','NUP50','ARVCF','SF3A1'],['exhaustive','filtered','adaptive'].map((m,i)=>({name:['Exhaustive','Filtered','Adaptive'][i],values:benchmark.inputs.slice(0,4).map(a=>a.results[m].median_ms),fill:[C.green,C.light,C.purple][i]})),20,'Median computation (ms)',{h:445});
foot(s,'Five fresh repeats per method after warm-up. Same input and settings. Hardware and background load affect timings.');

// 10 Large input and energy
s=slide('Maximum input and estimated energy',source+' These100000-base inputs are synthetic stress controls without biological truth. Motif-rich eligible49950 and edges50,baseline detailed99899. Estimated energy assumes15W for illustration. Frozen rich medians801.6242,450.3357,204.6002ms. Equal power makes reduction follow runtime.');
chart(s,['Motif-free control','Motif-rich control'],['exhaustive','filtered','adaptive'].map((m,i)=>({name:['Exhaustive','Filtered','Adaptive'][i],values:benchmark.inputs.slice(4,6).map(a=>a.results[m].median_ms),fill:[C.green,C.light,C.purple][i]})),900,'Median computation (ms)',{h:375});
text(s,'Estimated joules = assumed watts × milliseconds / 1000',64,550,1152,52,28,C.green,true);
foot(s,'100,000-base synthetic inputs have no accuracy labels. The 15 W example gives 12.024 / 6.755 / 3.069 J on motif-rich DNA. Power is assumed.');

// 11 App screenshot
s=slide('Guided local dashboard','Source image: qa/screenshots/part5-help-desktop.png, actual final browser QA on9October2026. The four-step path follows actual input, saved analysis and saved comparison. The interface uses short text and expandable details; its sample link downloads genuine ARVCF DNA.');
s.images.add({blob:new Uint8Array(await fs.readFile(path.join(root,'qa/screenshots/part5-help-desktop.png'))),contentType:'image/png',alt:'Actual EcoSplice green interface with four-step guidance and sample download',fit:'contain',position:{left:64,top:142,width:742,height:515}});
text(s,'Analyse and compare',853,166,363,72,32,C.green,true);
text(s,'Real scores, routes and repeated measurements',853,250,363,106,27);
text(s,'Validate and reports',853,395,363,78,32,C.green,true);
text(s,'Held-out metrics and SQLite history with consistent exports',853,487,363,139,27);

// 12 Demo
s=slide('One local launch after setup','Source: scripts/setup_local.py, scripts/start_local.py and docs/LOCAL_RELEASE.md. Python3.12 is the tested runtime. Source setup needsNode20.19+ or22.12+,ZIP hasprebuiltfrontendandrequiresnoNode. Internetfor dependency preparation once. Normalinference/labels/history/exportoffline. Occupiedport --port8766.');
text(s,'One-time setup',64,157,1152,55,32,C.green,true);
text(s,'setup-ecosplice.cmd',64,228,1152,50,32);
text(s,'Everyday launch',64,341,1152,55,32,C.green,true);
text(s,'start-ecosplice.cmd',64,412,1152,52,36);
text(s,'Open http://127.0.0.1:8765',64,503,1152,50,31);
foot(s,'The built frontend and API share one loopback Python process. Saved models, real demos and evaluation ship with the application.');

// 13 Limits
s=slide('Scientific limits and future work',source+' Future proposals only: variants,cryptic sites,intron pairing,calibration,broader datasets,quantization,Jetson/NPU,cloudoffload,federatedlearning. Current model canonical sampled chr22, scoresnotprobabilities, annotatednegativesnotproveninactive, homologyindependencenotestablished. UploadedFASTAhasnolabels.');
text(s,'Current evidence',64,154,500,60,33,C.green,true);
text(s,'Sampled chromosome 22 data\nCanonical GT and AG boundaries\nAdaptive quality can change\nEnergy uses assumed power',64,250,524,250,29);
text(s,'Future extensions',700,154,516,60,33,C.green,true);
text(s,'Broader independent evaluation\nCalibrated probabilities\nIntron pairing and variant effects\nMeasured power and acceleration',700,250,516,250,29);
foot(s,'Uploaded FASTA has no known answers. Results identify possible boundaries and require broader biological validation.');

const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(ppt)).save(candidatePath);
console.log(`Exported ${ppt.slides.items.length} editable slides with ${family}.`);
const finalPath=path.join(output,process.env.PRESENTATION_FILENAME || 'EcoSplice_Presentation.pptx');
await finalizePresentation({workspaceDir:root,candidatePath,finalPath,
  pythonExecutable:process.env.RUNTIME_PYTHON,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',
    '--require-native-table-slide','4','--require-native-table-slide','5','--require-native-table-slide','6'],
  explicitTotalSlideCount:13,requiredNativeTableOwnerSlides:[4,5,6],requiredNativeChartOwnerSlides:[8,9,10],
  materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[family]},
  verifyArtifactToolImport:true,receiptPath:path.join(build,path.basename(finalPath)+'.validation.json')});
const finalPresentation=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<finalPresentation.slides.items.length;i++) {
  const rendered=await finalPresentation.export({slide:finalPresentation.slides.items[i],format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await rendered.arrayBuffer()));
  console.log(`Rendered slide ${i+1}`);
}
console.log(`Final deck: ${finalPath}`);

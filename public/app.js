/* FinPilot Cloudflare Edition — no trackers, backend, paid APIs, or file uploads. */
(function(){
"use strict";
var PAGE_LABELS={overview:"Overview",sip:"SIP calculator",goal:"Goal planner",compound:"Compound growth",trading:"Trading insights",portfolio:"Portfolio review",categorizer:"Transactions",invoices:"Invoice matching",statements:"Statements",research:"Research summary"};
var DESCRIPTION="FinPilot does not provide financial, investment, tax or legal advice. It is an educational tool. Consult a licensed professional before making financial decisions.";
var state={page:"overview",exportRows:null,exportName:"finpilot.csv"};
var view=document.getElementById("view"),nav=document.getElementById("navigation"),sidebar=document.getElementById("sidebar");
var esc=function(s){return String(s===null||s===undefined?"":s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});};
var fmt=function(n){return Number(n).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});};
var pct=function(n){return (Number(n)*100).toFixed(1)+"%";};
var val=function(id){var el=document.getElementById(id);return el?el.value:"";};
var num=function(id){var v=Number(val(id));if(val(id).trim()===""||!Number.isFinite(v))throw Error("Enter a valid number for "+id.replace(/-/g," "));return v;};
var positive=function(n,label){if(n<0)throw Error(label+" cannot be negative.");return n;};
var range=function(n,min,max,label){if(n<min||n>max)throw Error(label+" must be between "+min+" and "+max+".");return n;};
var moneyField=function(id,label,value,step){return '<label class="field">'+label+'<input id="'+id+'" type="number" value="'+value+'" step="'+(step||"any")+'" min="0" required inputmode="decimal"></label>';};
var rateField=function(id,label,value){return '<label class="field">'+label+'<input id="'+id+'" type="number" value="'+value+'" min="-99" max="100" step="0.5" required inputmode="decimal"></label>';};
var action=function(id,text){return '<button class="btn primary" data-action="'+id+'" type="button">'+text+' <span aria-hidden="true">→</span></button>';};
var head=function(eyebrow,title,desc){return '<p class="eyebrow">'+eyebrow+'</p><h1 class="page-title">'+title+'</h1><p class="intro">'+desc+'</p>';};
var alertBox=function(text,cls){return '<div class="message '+(cls||"")+'">'+text+'</div>';};
var disclaimer=function(){return '<p class="disclaimer">'+DESCRIPTION+' Trading observations are historical and not buy or sell recommendations.</p>';};
var metric=function(label,value,sub){return '<div class="metric"><small>'+esc(label)+'</small><strong>'+esc(value)+'</strong>'+(sub?'<span>'+esc(sub)+'</span>':"")+'</div>';};
var panel=function(inner){return '<div class="panel">'+inner+'</div>';};
var inputFile=function(id,label,types){return '<label class="field wide">'+label+'<input class="file-input" id="'+id+'" type="file" accept="'+types+'"><small>Maximum 8 MB, and 5,000 rows for CSV. Processed locally in this browser.</small></label>';};
var shell=function(h,form,side,extra){return h+'<div class="two-col"><div>'+panel(form+'<div class="form-actions"></div>')+'</div><div>'+panel(side)+'</div></div><section class="result-area" id="results" aria-live="polite"></section>'+(extra||"")+disclaimer();};
function table(rows,columns){
 if(!rows.length)return alertBox("No rows to show.","warning");
 var cols=columns||Object.keys(rows[0]);
 return '<div class="data-wrap"><table class="data-table"><thead><tr>'+cols.map(function(c){return '<th scope="col">'+esc(c.replace(/_/g," "))+'</th>';}).join("")+'</tr></thead><tbody>'+rows.slice(0,100).map(function(r){return '<tr>'+cols.map(function(c){return '<td>'+esc(typeof r[c]==="number"?(Number.isFinite(r[c])?Math.round(r[c]*1e6)/1e6:"—"):r[c])+'</td>';}).join("")+'</tr>';}).join("")+'</tbody></table></div>'+(rows.length>100?'<p class="compact-note">Showing the first 100 of '+rows.length+' rows. Download the CSV for all results.</p>':"");
}
function result(content){var e=document.getElementById("results");if(e){e.innerHTML=content; e.scrollIntoView({behavior:"smooth",block:"nearest"});}}
function toast(t){var el=document.getElementById("toast");el.textContent=t;el.classList.add("show");clearTimeout(toast.id);toast.id=setTimeout(function(){el.classList.remove("show");},3200);}
function toggleMenu(open){sidebar.classList.toggle("open",open);document.getElementById("scrim").hidden=!open;document.getElementById("menu").setAttribute("aria-expanded",String(open));}
function overview(){
 var tools=[["sip","↗","SIP calculator","Plan recurring contributions and estimate potential growth."],["goal","◎","Goal planner","Calculate monthly savings needed for your future goal."],["compound","◈","Compound growth","Model compounding using transparent assumptions."],["portfolio","▦","Portfolio review","Inspect holdings and concentration from a CSV."],["categorizer","≡","Transaction review","Categorize records with auditable keyword rules."],["invoices","⇄","Invoice matching","Find possible payment matches without posting data."],["statements","▤","Statement comparison","Flag material changes between financial periods."],["trading","⌁","Historical insights","Calculate technical indicators from your price CSV."],["research","▧","Research summary","Produce a local extractive summary of pasted text."]];
 return '<div class="hero"><div class="hero-main"><span class="hero-tag"><span class="live-dot"></span> OPEN SOURCE · 100% FREE</span><h1 class="page-title">Financial clarity.<br><span class="gradient-text">Without complexity.</span></h1><p class="intro">A private workspace for investment planning, portfolio insights and accounting research. Everything runs directly in your browser.</p><div class="hero-actions"><button class="btn primary" data-page="sip">Start calculating →</button><button class="btn ghost" data-page="portfolio">Explore tools ↗</button></div></div><div class="hero-side"><div class="large-icon">◈</div><div><div class="kicker">Privacy first</div><h2>Your numbers.<br>Your browser.</h2><p>No paid API keys, financial-account connections, hidden cloud uploads or automated transactions.</p></div></div></div><div class="section-row"><h2 class="section-title">Explore your toolkit</h2><span class="tag">9 free tools</span></div><div class="tool-grid">'+tools.map(function(t){return '<button type="button" class="tool-card" data-page="'+t[0]+'"><span class="tool-icon">'+t[1]+'</span><strong>'+t[2]+'</strong><p>'+t[3]+'</p><span class="arrow">Explore →</span></button>';}).join("")+'</div>'+alertBox('<strong>Cloudflare edition:</strong> Streamlit and Python cannot run as a standard static Worker. Calculators and CSV analysis are browser-based. Trading uses a supplied historical price CSV rather than live Yahoo data, and research summary accepts pasted text rather than PDFs. The original Python version remains in the repository.')+disclaimer();
}
function calculatorPage(which){
 if(which==="sip")return shell(head("INVESTMENT PLANNING","SIP calculator","Project the future value of recurring investments using a constant assumed annual return."),'<h2>SIP assumptions</h2><div class="form-grid">'+moneyField("monthly","Monthly contribution",500,50)+moneyField("initial","Initial investment",0,100)+rateField("rate","Annual return (%)",8)+moneyField("years","Years",10,1)+'</div><div class="form-actions">'+action("sip","Calculate return")+'</div>','<h2>How it works</h2><p class="panel-desc">Your initial investment grows over time. Each monthly contribution compounds from the end of its contribution period.</p>'+alertBox("Assumes a constant monthly rate. Taxes, fees and market volatility are excluded.")+'<ul class="feature-list"><li>Monthly contributions at period end</li><li>No brokerage account required</li><li>Transparent educational model</li></ul>');
 if(which==="goal")return shell(head("INVESTMENT PLANNING","Goal planner","Find the estimated monthly contribution needed to reach a future financial goal."),'<h2>Your goal</h2><div class="form-grid">'+moneyField("target","Goal in today’s money",100000,1000)+moneyField("current","Current savings",10000,1000)+moneyField("years","Years until goal",8,1)+rateField("rate","Annual return (%)",7)+rateField("inflation","Annual inflation (%)",3)+'</div><div class="form-actions">'+action("goal","Plan my goal")+'</div>','<h2>Plan ahead</h2><p class="panel-desc">The calculator adjusts the target for inflation and estimates how recurring monthly savings may fill the remaining gap.</p>'+alertBox("Future returns and inflation are not guaranteed.")+'<ul class="feature-list"><li>Inflation-adjusted target</li><li>Accounts for existing savings</li><li>Contributions at each month’s end</li></ul>');
 return shell(head("INVESTMENT PLANNING","Compound growth","See how a starting amount changes under monthly compounding assumptions."),'<h2>Growth assumptions</h2><div class="form-grid">'+moneyField("principal","Starting principal",10000,500)+rateField("rate","Annual rate (%)",7)+moneyField("years","Years",10,1)+'</div><div class="form-actions">'+action("compound","Calculate growth")+'</div>','<h2>Power of compounding</h2><p class="panel-desc">The calculation compounds interest 12 times per year and assumes the rate stays fixed.</p>'+alertBox("Illustrative math only. Taxes, fees, inflation and market volatility are excluded.")+'<ul class="feature-list"><li>Monthly compounding</li><li>No hidden fees or API calls</li><li>Clear growth breakdown</li></ul>');
}
function csvPage(which){
 if(which==="portfolio")return shell(head("PORTFOLIO ANALYSIS","Portfolio concentration","Review positions and identify concentration using a locally processed holdings CSV."),'<h2>Upload holdings</h2><p class="subtle">Required columns: symbol (or ticker), market_value (or value). Optional: asset_class.</p><div class="form-grid top-spacing">'+inputFile("file-portfolio","Holdings CSV",".csv,text/csv")+'</div><div class="form-actions">'+action("portfolio","Review portfolio")+'<button class="btn ghost" data-action="sample-portfolio">Use sample data</button></div>','<h2>What is measured?</h2><ul class="feature-list"><li>Largest and top-three position weights</li><li>Gross and net portfolio exposure</li><li>Concentration and short-exposure flags</li><li>Asset-class concentration where supplied</li></ul>'+alertBox("Concentration is not a prediction of portfolio performance."));
 if(which==="categorizer")return shell(head("ACCOUNTING TOOLS","Transaction categorizer","Organize bank and ledger transactions using auditable keyword classification."),'<h2>Review transactions</h2><p class="subtle">Requires description and either amount or debit/credit. Date is recommended.</p><div class="form-grid top-spacing">'+inputFile("file-categorizer","Transactions CSV",".csv,text/csv")+'<label class="field wide">Jurisdiction label<input id="jurisdiction" type="text" maxlength="80" value="unspecified"></label></div><div class="form-actions">'+action("categorizer","Categorize records")+'<button class="btn ghost" data-action="sample-categorizer">Use sample data</button></div>','<h2>Conservative by design</h2><ul class="feature-list"><li>Transparent local keyword rules</li><li>Potential duplicates and outliers flagged</li><li>Low-confidence entries require review</li><li>Never files taxes or posts to a ledger</li></ul>');
 if(which==="invoices")return shell(head("ACCOUNTING TOOLS","Invoice reconciliation","Match potential invoice payments conservatively for manual review."),'<h2>Two CSV files</h2><p class="subtle">Invoices: invoice_id, amount. Payments: reference, amount.</p><div class="form-grid top-spacing">'+inputFile("file-invoices","Invoices CSV",".csv,text/csv") + inputFile("file-payments","Payments CSV",".csv,text/csv")+'<label class="field">Amount tolerance<input id="tolerance" type="number" min="0" step=".01" value=".01"></label></div><div class="form-actions">'+action("invoices","Match invoices")+'<button class="btn ghost" data-action="sample-invoices">Use sample data</button></div>','<h2>Matching policy</h2><ul class="feature-list"><li>Invoice ID and amount match preferred</li><li>Unique amount-only matches flagged</li><li>Ambiguous matches remain unmatched</li><li>Never settles or posts payments</li></ul>');
 return shell(head("ACCOUNTING TOOLS","Statement comparison","Compare period-over-period amounts and flag potentially material changes."),'<h2>Upload statement</h2><p class="subtle">Required columns: line_item, current_period, prior_period.</p><div class="form-grid top-spacing">'+inputFile("file-statements","Financial statement CSV",".csv,text/csv")+'<label class="field wide">Flag changes at or above (%)<input id="threshold" min="1" max="200" step="1" type="number" value="25"></label></div><div class="form-actions">'+action("statements","Compare periods")+'<button class="btn ghost" data-action="sample-statements">Use sample data</button></div>','<h2>Clear comparisons</h2><ul class="feature-list"><li>Absolute period-over-period change</li><li>Percentage changes</li><li>Missing amounts or sign changes</li><li>Review flags for large changes</li></ul>'+alertBox("Comparison provides no audit opinion or accounting-policy conclusion."));
}
function tradingPage(){
 return shell(head("MARKET RESEARCH","Historical trading insights","Upload historical OHLCV price data to calculate technical indicators. No live market feeds or order placement."),'<h2>Analyze historical prices</h2><p class="subtle">Upload CSV with columns: date, open, high, low, close, volume. At least 35 daily price rows.</p><div class="form-grid top-spacing">'+inputFile("file-trading","Historical price CSV",".csv,text/csv")+'</div><div class="form-actions">'+action("trading","Analyze history")+'</div>','<h2>Included indicators</h2><ul class="feature-list"><li>20- and 50-session moving average</li><li>EMA 12 and EMA 26</li><li>RSI 14 and MACD</li><li>20-session annualized volatility</li></ul>'+alertBox("Live Yahoo/yfinance and RSS features require the original Python app. This Cloudflare edition only analyzes your uploaded CSV.","warning"));
}
function researchPage(){
 return shell(head("RESEARCH TOOLS","Research text summary","Extract important sentences from pasted research text using a transparent, local frequency-based method."),'<h2>Paste your research text</h2><label class="field">Research text<textarea id="research-text" placeholder="Paste a report excerpt or research article here. This text stays in your browser."></textarea></label><div class="form-grid top-spacing"><label class="field">Summary sentences<input type="number" id="sentences" min="3" max="12" value="7"></label></div><div class="form-actions">'+action("research","Summarize text")+'</div>','<h2>How this version works</h2><ul class="feature-list"><li>Frequency-weighted extractive summary</li><li>Original sentences, no AI hallucination</li><li>Text stays in your browser</li></ul>'+alertBox("PDF extraction is only supported by the original Python app, not this static Cloudflare edition. Extract the text from a PDF first, then paste it here.","warning"));
}
function page(p){if(p==="overview")return overview();if(["sip","goal","compound"].includes(p))return calculatorPage(p);if(["portfolio","categorizer","invoices","statements"].includes(p))return csvPage(p);if(p==="trading")return tradingPage();return researchPage();}
function setPage(p){if(!PAGE_LABELS[p])p="overview";state.page=p;state.exportRows=null;view.innerHTML=page(p);document.getElementById("breadcrumb").textContent=PAGE_LABELS[p];document.title=PAGE_LABELS[p]+" | FinPilot";nav.querySelectorAll("[data-page]").forEach(function(n){n.classList.toggle("active",n.dataset.page===p);if(n.dataset.page===p)n.setAttribute("aria-current","page");else n.removeAttribute("aria-current");});toggleMenu(false);history.replaceState(null,"","#"+p);window.scrollTo({top:0,behavior:"auto"});}
function fixed(n){return Math.round((n+Number.EPSILON)*100)/100;}
function calc(which){
 var yrs=range(positive(num("years"),"Years"),0,100,"Years"),rate=range(num("rate"),-99,100,"Annual rate"),months=Math.round(yrs*12),r=rate/1200;
 if(which==="sip"){
  var monthly=positive(num("monthly"),"Monthly contribution"),initial=positive(num("initial"),"Initial investment");
  var future=initial*Math.pow(1+r,months)+(months===0?0:Math.abs(r)<1e-12?monthly*months:monthly*(Math.pow(1+r,months)-1)/r);
  var contributed=initial+monthly*months;
  result('<h2 class="section-title">Your projection</h2><div class="metrics">'+metric("Total contributed",fmt(contributed))+metric("Estimated future value",fmt(future))+metric("Estimated growth",fmt(future-contributed))+'</div>'+alertBox("Constant user-supplied return. Taxes, fees, inflation, and volatility are excluded."));return;
 }
 if(which==="compound"){
  var principal=positive(num("principal"),"Principal"),value=principal*Math.pow(1+rate/1200,months);
  result('<h2 class="section-title">Your projection</h2><div class="metrics">'+metric("Initial principal",fmt(principal))+metric("Estimated future value",fmt(value))+metric("Estimated growth",fmt(value-principal))+'</div>'+alertBox("Constant user-provided rate; taxes, fees, and market volatility are excluded."));return;
 }
 var target=positive(num("target"),"Target"),current=positive(num("current"),"Current savings"),inflation=range(num("inflation"),-99,100,"Inflation");
 var futureTarget=target*Math.pow(1+inflation/100,yrs),currentFuture=current*Math.pow(1+r,months),gap=Math.max(0,futureTarget-currentFuture);
 var required=months===0?gap:Math.abs(r)<1e-12?gap/months:gap/((Math.pow(1+r,months)-1)/r);
 result('<h2 class="section-title">Goal projection</h2><div class="metrics">'+metric("Inflation-adjusted target",fmt(futureTarget))+metric("Required monthly contribution",fmt(required))+metric("Future value of savings",fmt(currentFuture))+'</div>'+alertBox(gap===0?"Current savings could already fund this goal under these assumptions.":"Illustrative projection only; future returns and inflation are not guaranteed.","success"));
}
function csvParse(text){
 var rows=[],row=[],cell="",quoted=false,i=0;
 text=String(text).replace(/^\uFEFF/,"");
 for(i=0;i<text.length;i++){var c=text[i];if(quoted){if(c==='"'&&text[i+1]==='"'){cell+='"';i++;}else if(c==='"'){quoted=false;}else{cell+=c;}}else if(c==='"'&&cell===""){quoted=true;}else if(c===","){row.push(cell);cell="";}else if(c==="\n"||c==="\r"){if(c==="\r"&&text[i+1]==="\n")i++;row.push(cell);if(row.some(function(x){return x.trim()!=="";}))rows.push(row);row=[];cell="";if(rows.length>5002)throw Error("CSV exceeds the 5,000-row limit.");}else{cell+=c;}}
 if(quoted)throw Error("CSV contains an unclosed quoted field.");row.push(cell);if(row.some(function(x){return x.trim()!=="";}))rows.push(row);
 if(rows.length<2)throw Error("CSV needs a header row and at least one record.");
 var hdr=rows.shift().map(function(x){return x.trim().toLowerCase().replace(/^\uFEFF/,"");});if(new Set(hdr).size!==hdr.length)throw Error("CSV has duplicate column names.");
 var out=rows.map(function(r){var obj={};hdr.forEach(function(k,i){obj[k]=r[i]===undefined?"":r[i].trim();});return obj;});
 if(out.length>5000)throw Error("CSV exceeds 5,000 rows.");return out;
}
function parseSource(text){if(new Blob([text]).size>8*1024*1024)throw Error("Maximum file size is 8 MB.");return csvParse(text);}
async function loadCSV(id){var el=document.getElementById(id),file=el&&el.files&&el.files[0];if(!file)throw Error("Select a CSV file first, or choose sample data.");if(file.size>8*1024*1024)throw Error("Maximum file size is 8 MB.");if(!/\.csv$/i.test(file.name))throw Error("Only .csv files are supported.");return parseSource(await file.text());}
function col(rows,aliases){var ks=Object.keys(rows[0]||{});for(var a of aliases){var k=ks.find(function(k){return k.trim().toLowerCase()===a;});if(k)return k;}return null;}
function toNum(x){if(x===""||x==null)return NaN;var n=Number(String(x).replace(/,/g,""));return Number.isFinite(n)?n:NaN;}
function exportButton(rows,name){state.exportRows=rows;state.exportName=name;return '<div class="form-actions"><button type="button" class="btn ghost" data-action="download">Download all results (.csv) ↓</button></div>';}
function download(){
 var rows=state.exportRows;if(!rows||!rows.length)return;var cols=Object.keys(rows[0]);
 var serialize=function(c){var v=String(c===null||c===undefined?"":c);if(/^[=+@\t\r]/.test(v))v="'"+v;return '"'+v.replace(/"/g,'""')+'"';};
 var csv="\uFEFF"+cols.map(serialize).join(",")+"\r\n"+rows.map(function(r){return cols.map(function(c){return serialize(r[c]);}).join(",");}).join("\r\n");
 var uri=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));var a=document.createElement("a");a.href=uri;a.download=state.exportName;document.body.append(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(uri);},1000);
}
var sample={
portfolio:"symbol,market_value,asset_class\nAAPL,4200,US Equity\nMSFT,2400,US Equity\nBND,1800,Bond ETF\nCASH,600,Cash",
categorizer:"date,description,debit,credit,balance\n2026-01-02,Client payment invoice 1042,0,2500,2500\n2026-01-03,Office rent January,900,0,1600\n2026-01-04,GitHub subscription,10,0,1590\n2026-01-05,Unknown merchant ZXQ,75,0,1515\n2026-01-05,Unknown merchant ZXQ,75,0,1440\n2026-01-07,Electricity bill,120,0,1320\n2026-01-09,Professional accounting consultation,200,0,1120",
invoices:"invoice_id,vendor,amount,due_date\nINV-1001,Northwind Supplies,250.00,2026-01-31\nINV-1002,Contoso Hosting,89.99,2026-02-05\nINV-1003,Example Legal,500.00,2026-02-10",
payments:"date,reference,amount\n2026-01-20,Payment for INV-1001,250.00\n2026-02-01,Contoso monthly charge,89.99\n2026-02-07,Unrelated payment,120.00",
statements:"line_item,current_period,prior_period\nRevenue,125000,100000\nCost of sales,-70000,-60000\nOperating expenses,-42000,-32000\nNet income,13000,8000\nCash,24000,30000"
};
var ruleSet={
income:["salary","payroll","client payment","invoice paid","interest credit"],
rent_and_utilities:["rent","electric","electricity","water bill","gas bill","internet"],
software_and_subscriptions:["hosting","software","subscription","github","microsoft","google workspace"],
travel_and_transport:["uber","lyft","taxi","bus","train","flight","fuel","petrol"],
food_and_meals:["restaurant","cafe","food","grocery","supermarket","meal"],
bank_and_finance_fees:["bank fee","service charge","late fee","atm fee","transfer fee"],
taxes_and_government:["tax","vat","gst","government fee","customs"],
office_and_supplies:["stationery","office supply","printer","paper","courier"],
professional_services:["consulting","legal","accounting","audit","freelancer"],
healthcare:["hospital","clinic","pharmacy","doctor","medical"]
};
function portfolio(rows){
 var s=col(rows,["symbol","ticker","security","name"]),v=col(rows,["market_value","market value","value","position_value"]),a=col(rows,["asset_class","asset class","category","sector"]);
 if(!s||!v)throw Error("Holdings CSV needs symbol/ticker and market_value/value columns.");
 var positions=rows.map(function(r){return {symbol:r[s]||"UNKNOWN",market_value:toNum(r[v]),asset_class:a?r[a]||"Unspecified":"Unspecified"};}).filter(function(r){return Number.isFinite(r.market_value);});
 var gross=positions.reduce(function(n,r){return n+Math.abs(r.market_value);},0);if(gross<=0)throw Error("Gross exposure must exceed zero.");
 positions.forEach(function(r){r.gross_weight=Math.abs(r.market_value)/gross;});positions.sort(function(a,b){return b.gross_weight-a.gross_weight;});
 var top1=positions[0].gross_weight,top3=positions.slice(0,3).reduce(function(n,r){return n+r.gross_weight;},0),net=positions.reduce(function(n,r){return n+r.market_value;},0);
 var flags=[];if(top1>=.25)flags.push({severity:top1>=.4?"high":"moderate",detail:"Largest position represents "+pct(top1)+" of gross exposure."});
 if(top3>=.6)flags.push({severity:"moderate",detail:"Top three positions represent "+pct(top3)+" of gross exposure."});
 var short=positions.filter(function(r){return r.market_value<0;}).reduce(function(n,r){return n+Math.abs(r.market_value);},0)/gross;
 if(short>0)flags.push({severity:"informational",detail:"Short positions represent "+pct(short)+" of gross exposure."});
 if(a){var groups={};positions.forEach(function(r){groups[r.asset_class]=(groups[r.asset_class]||0)+r.gross_weight;});var max=Math.max.apply(null,Object.values(groups));if(max>=.7)flags.push({severity:"moderate",detail:"Largest asset class represents "+pct(max)+" of gross exposure."});}
 var clean=positions.map(function(p){return {symbol:p.symbol,market_value:fixed(p.market_value),asset_class:p.asset_class,gross_weight_percent:fixed(p.gross_weight*100)};});
 result('<h2 class="section-title">Portfolio analysis</h2><div class="metrics">'+metric("Positions",positions.length)+metric("Largest position",pct(top1))+metric("Top three",pct(top3))+'</div><div class="section-row"><h2 class="section-title">Risk flags</h2></div>'+(flags.length?table(flags):alertBox("No concentration threshold was triggered.","success"))+'<div class="section-row"><h2 class="section-title">Top holdings</h2></div>'+table(clean)+exportButton(clean,"finpilot-portfolio.csv")+alertBox("Gross exposure: "+fmt(gross)+" · Net exposure: "+fmt(net)+". This is not a prediction or buy/sell recommendation."));
}
function median(nums){var sorted=nums.slice().sort(function(a,b){return a-b;});if(!sorted.length)return 0;var m=Math.floor(sorted.length/2);return sorted.length%2?sorted[m]:(sorted[m-1]+sorted[m])/2;}
function quantile(nums,q){var sorted=nums.slice().sort(function(a,b){return a-b;});if(!sorted.length)return 0;var idx=(sorted.length-1)*q,lo=Math.floor(idx),hi=Math.ceil(idx);return sorted[lo]+(sorted[hi]-sorted[lo])*(idx-lo);}
function transactions(rows){
 var dateCol=col(rows,["date","transaction date","posted date","value date"]),descCol=col(rows,["description","details","narration","memo","merchant","transaction"]),amountCol=col(rows,["amount","net amount","transaction amount"]),debitCol=col(rows,["debit","withdrawal","money out","paid out"]),creditCol=col(rows,["credit","deposit","money in","paid in"]);
 if(!descCol||(!amountCol&&!debitCol&&!creditCol))throw Error("CSV requires description and either amount or debit/credit columns.");
 var dates={},groups={},data=rows.map(function(r,i){
 var amount=amountCol?toNum(r[amountCol]):Math.abs(toNum(r[creditCol]||0)||0)-Math.abs(toNum(r[debitCol]||0)||0);if(!Number.isFinite(amount))amount=0;
 var description=r[descCol]||"",matches=[],text=description.toLowerCase();
 Object.keys(ruleSet).forEach(function(cat){ruleSet[cat].forEach(function(keyword){if(text.includes(keyword))matches.push({cat:cat,keyword:keyword});});});
 matches.sort(function(a,b){return b.keyword.length-a.keyword.length;});var categories=new Set(matches.map(function(m){return m.cat;}));
 var category=matches.length?matches[0].cat:"uncategorized",confidence=matches.length?(categories.size===1?.95:.65):0,date=dateCol?r[dateCol]:"";
 var validDate=!!date&&!Number.isNaN(Date.parse(date));
 return {date:validDate?date:"",description:description,amount:fixed(amount),category:category,confidence:confidence,reason:matches.length?"Matched keyword '"+matches[0].keyword+"'":"No keyword rule matched",method:"keyword",anomaly_reasons:"",needs_human_review:false,source_row:i};
 });
 var nums=data.map(function(r){return Math.abs(r.amount);}).filter(function(n){return n>0;}),threshold=Math.max(median(nums)*5,nums.length>=5?quantile(nums,.95):0);
 data.forEach(function(r){var k=r.date+"|"+r.description+"|"+r.amount;dates[k]=(dates[k]||0)+1;});
 data.forEach(function(r){var reasons=[],k=r.date+"|"+r.description+"|"+r.amount;
 if(!r.description.trim())reasons.push("missing description");if(dates[k]>1)reasons.push("possible duplicate");
 if(threshold>0&&Math.abs(r.amount)>=threshold)reasons.push("unusually high value");
 if(r.category==="uncategorized")reasons.push("uncategorized");if(r.confidence<.75)reasons.push("low classification confidence");
 if(!r.date)reasons.push("missing or invalid date");
 r.anomaly_reasons=reasons.join("; ");r.needs_human_review=reasons.length>0;
 groups[r.category]=(groups[r.category]||0)+1;
 });
 var inflow=data.reduce(function(a,r){return a+Math.max(r.amount,0);},0),outflow=data.reduce(function(a,r){return a+Math.max(-r.amount,0);},0),review=data.filter(function(r){return r.needs_human_review;}).length;
 result('<h2 class="section-title">Categorization results</h2><div class="metrics">'+metric("Transactions",data.length)+metric("Net movement",fmt(inflow-outflow))+metric("Need human review",review)+'</div><div class="section-row"><h2 class="section-title">Classified transactions</h2></div>'+table(data,["date","description","amount","category","confidence","anomaly_reasons"])+exportButton(data,"finpilot-transactions.csv")+alertBox('<strong>Draft review note — '+esc(val("jurisdiction").slice(0,80)||"unspecified")+'.</strong> '+data.length+' transactions, '+review+' flagged for human review. Confirm balances and classifications against source records. No tax calculation, filing, payment or ledger posting was performed.'));
}
function invoices(inv,pay){
 var id=col(inv,["invoice_id","invoice id","invoice","reference"]),ia=col(inv,["amount","invoice_amount","invoice amount","total"]),ref=col(pay,["reference","description","memo","narration"]),pa=col(pay,["amount","payment_amount","payment amount","credit"]);
 if(!id||!ia||!ref||!pa)throw Error("Missing invoice ID/amount or payment reference/amount columns.");
 var tol=positive(num("tolerance"),"Tolerance"),used=new Set(),out=inv.map(function(r,i){
 var invoiceId=(r[id]||"").trim(),amount=toNum(r[ia]),matches=[];
 if(Number.isFinite(amount)){
  pay.forEach(function(p,j){if(!used.has(j)&&Number.isFinite(toNum(p[pa]))&&Math.abs(toNum(p[pa])-amount)<=tol&&invoiceId&&(p[ref]||"").toLowerCase().includes(invoiceId.toLowerCase()))matches.push(j);});
  if(!matches.length){var only=pay.map(function(p,j){return !used.has(j)&&Number.isFinite(toNum(p[pa]))&&Math.abs(toNum(p[pa])-amount)<=tol?j:-1;}).filter(function(j){return j>=0;});if(only.length===1)matches=only;}
 }
 var match=matches.length===1,method=match?((pay[matches[0]][ref]||"").toLowerCase().includes(invoiceId.toLowerCase())?"invoice_id_and_amount":"unique_amount_only"):"";
 if(match)used.add(matches[0]);return {invoice_row:i,invoice_id:invoiceId,invoice_amount:Number.isFinite(amount)?amount:"",status:match?"matched":matches.length>1?"ambiguous":"unmatched",payment_row:match?matches[0]:"",match_method:method,needs_human_review:method!=="invoice_id_and_amount"};
 });
 var matched=out.filter(function(r){return r.status==="matched";}).length;
 result('<h2 class="section-title">Matching results</h2><div class="metrics">'+metric("Invoices",inv.length)+metric("Matched",matched)+metric("Unmatched / ambiguous",inv.length-matched)+'</div><div class="section-row"><h2 class="section-title">Candidates for review</h2></div>'+table(out)+exportButton(out,"finpilot-invoice-matches.csv")+alertBox("Payment matches are candidates for human review, not evidence of settlement. Unused payment rows: "+(pay.length-used.size)+"."));
}
function statements(rows){
 var item=col(rows,["line_item"]),cur=col(rows,["current_period"]),prior=col(rows,["prior_period"]);
 if(!item||!cur||!prior)throw Error("Required columns: line_item, current_period and prior_period.");
 var threshold=range(num("threshold"),1,200,"Threshold"),out=rows.map(function(r){
 var c=toNum(r[cur]),p=toNum(r[prior]),diff=c-p,percent=Number.isFinite(p)&&p!==0?diff/Math.abs(p)*100:NaN,flags=[];
 if(!Number.isFinite(c)||!Number.isFinite(p))flags.push("missing numeric value");
 else if(c*p<0)flags.push("sign change");
 if(Number.isFinite(percent)&&Math.abs(percent)>=threshold)flags.push("change at or above "+threshold.toFixed(1)+"%");
 return {line_item:r[item]||"Unspecified",current_period:Number.isFinite(c)?c:"",prior_period:Number.isFinite(p)?p:"",absolute_change:Number.isFinite(diff)?fixed(diff):"",percent_change:Number.isFinite(percent)?fixed(percent):"",review_flag:flags.join("; ")};
 });var flagged=out.filter(function(r){return r.review_flag;}).length;
 result('<h2 class="section-title">Statement comparison</h2><div class="metrics">'+metric("Line items",out.length)+metric("Flagged items",flagged)+metric("Review threshold",threshold+"%")+'</div><div class="section-row"><h2 class="section-title">Period changes</h2></div>'+table(out)+exportButton(out,"finpilot-statements.csv")+alertBox("Arithmetic review only. No audit assurance, accounting-policy conclusion or valuation is provided."));
}
function ema(values,period){var k=2/(period+1),out=[],last=values[0];values.forEach(function(v,i){if(i===0)last=v;else last=(v-last)*k+last;out.push(last);});return out;}
function trading(rows){
 var closeCol=col(rows,["close"]),dateCol=col(rows,["date"]),open=col(rows,["open"]),high=col(rows,["high"]),low=col(rows,["low"]),volume=col(rows,["volume"]);
 if(!closeCol||!open||!high||!low||!volume)throw Error("CSV needs open, high, low, close and volume columns.");
 var data=rows.map(function(r,i){return {date:dateCol?r[dateCol]:String(i),close:toNum(r[closeCol])};}).filter(function(r){return Number.isFinite(r.close)&&r.close>0;});
 if(dateCol)data.sort(function(a,b){return String(a.date).localeCompare(String(b.date));});
 if(data.length<35)throw Error("At least 35 valid price rows are required.");
 var prices=data.map(function(r){return r.close;}),n=prices.length,latest=prices[n-1],sma=function(k){return n>=k?prices.slice(-k).reduce(function(a,b){return a+b;},0)/k:NaN;},fast=ema(prices,12),slow=ema(prices,26),macd=fast.map(function(v,i){return v-slow[i];}),signal=ema(macd,9);
 var gain=0,loss=0,gains=[],losses=[];for(var i=1;i<n;i++){var d=prices[i]-prices[i-1];gains.push(Math.max(d,0));losses.push(Math.max(-d,0));}
 for(i=0;i<14;i++){gain+=gains[i];loss+=losses[i];}gain/=14;loss/=14;
 for(i=14;i<gains.length;i++){gain=(gain*13+gains[i])/14;loss=(loss*13+losses[i])/14;}
 var rsi=loss===0?100:100-100/(1+gain/loss),returns=[];
 for(i=1;i<n;i++)returns.push(prices[i]/prices[i-1]-1);var recent=returns.slice(-20),avg=recent.reduce(function(a,b){return a+b;},0)/recent.length,variance=recent.reduce(function(a,b){return a+Math.pow(b-avg,2);},0)/(recent.length-1),vol=Math.sqrt(variance)*Math.sqrt(252),ma20=sma(20),ma50=sma(50);
 var notes=["Latest close is "+(latest>ma20?"above":"below")+" its 20-period average.",Number.isFinite(ma50)?"The 20-period average is "+(ma20>ma50?"above":"below")+" the 50-period average.":"A 50-period average requires at least 50 rows.","RSI(14) is "+rsi.toFixed(2)+".","MACD is "+(macd[n-1]>signal[n-1]?"above":"below")+" its signal line.","Annualized 20-period volatility is approximately "+pct(vol)+".","Historical indicators do not forecast future returns."];
 var snapshot=[{as_of:data[n-1].date,close:fixed(latest),one_day_change_percent:fixed((latest/prices[n-2]-1)*100),sma20:fixed(ma20),sma50:Number.isFinite(ma50)?fixed(ma50):"",ema12:fixed(fast[n-1]),ema26:fixed(slow[n-1]),rsi14:fixed(rsi),macd:fixed(macd[n-1]),macd_signal:fixed(signal[n-1]),volatility20_annualized:fixed(vol),rows_analyzed:n}];
 var chartData=prices.slice(-36),min=Math.min.apply(null,chartData),max=Math.max.apply(null,chartData),spread=Math.max(0.000001,max-min);
 var chart='<div class="chart" role="img" aria-label="Recent closing prices shown as a bar chart">'+chartData.map(function(v){return '<div class="bar" style="--h:'+(20+80*(v-min)/spread).toFixed(2)+'%"></div>';}).join("")+'</div>';
 result('<h2 class="section-title">Historical insights</h2><div class="metrics">'+metric("Latest close",fmt(latest))+metric("RSI (14)",rsi.toFixed(2))+metric("Annualized volatility",pct(vol))+'</div>'+panel('<h2>Recent closes</h2>'+chart)+'<div class="section-row"><h2 class="section-title">Indicator snapshot</h2></div>'+table(snapshot)+'<div class="section-row"><h2 class="section-title">What the data indicates</h2></div>'+panel('<ul class="feature-list">'+notes.map(function(s){return '<li>'+esc(s)+'</li>';}).join("")+'</ul>')+exportButton(snapshot,"finpilot-indicators.csv"));
}
function research(){
 var text=val("research-text").trim(),count=range(num("sentences"),3,12,"Sentences");if(text.length<100)throw Error("Paste at least 100 characters of source text.");if(text.length>150000)throw Error("Maximum text length is 150,000 characters.");
 var sentences=text.replace(/\s+/g," ").split(/(?<=[.!?])\s+/).filter(function(x){return x.trim().length>=40;});if(!sentences.length)sentences=[text.slice(0,1000)];
 var stop=new Set("a an and are as at be been by for from has have in into is it its of on or that the their this to was were will with we our you your".split(" "));
 var words=function(t){return (t.match(/[A-Za-z][A-Za-z0-9'-]{2,}/g)||[]).map(function(w){return w.toLowerCase();}).filter(function(w){return !stop.has(w);});};
 var freq={},all=words(text);all.forEach(function(w){freq[w]=(freq[w]||0)+1;});var max=Math.max(1,...Object.values(freq));
 var scored=sentences.map(function(s,i){var ws=words(s);return {sentence:s,index:i,score:ws.length&&ws.length<=80?ws.reduce(function(t,w){return t+(freq[w]||0)/max;},0)/ws.length:-1};}).filter(function(x){return x.score>=0;});
 scored.sort(function(a,b){return b.score-a.score;});var selected=scored.slice(0,count).sort(function(a,b){return a.index-b.index;});
 if(!selected.length)selected=[{sentence:text.slice(0,1000)}];
 result('<h2 class="section-title">Extractive summary</h2>'+panel('<ol class="feature-list">'+selected.map(function(s){return '<li>'+esc(s.sentence)+'</li>';}).join("")+'</ol>')+alertBox("This is a frequency-based extractive summary. It cannot validate methodology, accuracy, numerical claims, conflicts of interest or data quality."));
}
async function run(which,data){
 switch(which){
 case "sip":case "goal":case "compound":calc(which);return;
 case "portfolio":portfolio(data||await loadCSV("file-portfolio"));return;
 case "categorizer":transactions(data||await loadCSV("file-categorizer"));return;
 case "invoices":{var files=data||[await loadCSV("file-invoices"),await loadCSV("file-payments")];invoices(files[0],files[1]);return;}
 case "statements":statements(data||await loadCSV("file-statements"));return;
 case "trading":trading(data||await loadCSV("file-trading"));return;
 case "research":research();return;
 }
}
document.addEventListener("click",async function(e){
 var link=e.target.closest("[data-page]");if(link){setPage(link.dataset.page);return;}
 var b=e.target.closest("[data-action]");if(!b)return;
 var id=b.dataset.action;if(id==="download"){download();return;}
 if(id.startsWith("sample-")){var sampleId=id.slice(7);try{if(sampleId==="invoices")await run(sampleId,[parseSource(sample.invoices),parseSource(sample.payments)]);else await run(sampleId,parseSource(sample[sampleId]));}catch(err){result(alertBox(esc(err.message),"error"));}return;}
 b.disabled=true;var old=b.textContent;b.textContent="Processing…";
 try{await run(id);}catch(err){result(alertBox(esc(err&&err.message?err.message:"The file could not be processed."),"error"));}finally{b.disabled=false;b.textContent=old;}
});
document.getElementById("menu").addEventListener("click",function(){toggleMenu(!sidebar.classList.contains("open"));});
document.getElementById("scrim").addEventListener("click",function(){toggleMenu(false);});
document.addEventListener("keydown",function(e){if(e.key==="Escape")toggleMenu(false);});
window.addEventListener("hashchange",function(){var p=location.hash.slice(1);if(p!==state.page)setPage(p);});
setPage(location.hash.slice(1)||"overview");
})();